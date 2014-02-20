import cStringIO

from common.workload import Workload as BaseWorkload

from result import GatlingStdoutParser, GatlingResult
from stats import Stats


class Workload(BaseWorkload):
    """
    Class that handles a Gatling cloud workload.
    """

    def __init__(self, client, pool, config):
        """
        Inits the workload. Needs a salt local client, minion pool and
        a configuration dictionary

        @param client - cloud_workloads.remote.client.Client
        @param pool - cloud_workloads.remote.pool.MinionPool
        @param config - dict

        """
        super(Workload, self).__init__(client, pool, config)
        self._results = []
        self.webheads = None

    @property
    def name(self):
        """
        Returns name of the workload.

        :returns: String name of the workload

        """
        return "Gatling"

    @property
    def users_start(self):
        """
        Returns the starting number of users per webhead.
        Taken from the config.

        :returns: Integer starting number of users

        """
        return int(self.config['users_start'])

    @property
    def users_step(self):
        """
        Returns the number of users per webhead to increase with
        every iteration.
        Taken from the config.

        :returns: Integer number of users per webhead to increase

        """
        return int(self.config['users_step'])

    @property
    def duration(self):
        """
        Returns the number of seconds over which to run scenarios
        with the indicated number of users in seconds.
        Taken from the config.

        :returns:  Integer number of seconds

        """
        return int(self.config['duration'])

    def get_webheads(self):
        """
        Returns the list of webheads.
        Taken from the config.

        :returns: List

        """
        if self.webheads is None:
            minions = self.minions_with_role(self.config['webhead_role'])
            ips_dict = self.client.get_ips(minions)
            self.webheads = [self.config['webhead_url'] % ips[0]
                             for ips in ips_dict.itervalues()]

        return self.webheads

    @property
    def best_run(self):
        """
        Returns the second to last iteration if there are more than one.
        The testing stops when an iteration fails.

        Returns the only iteration if only one.  The only iteration fails.

        Returns None otherwise (test probably hasn't been run yet.

        :returns: [GatlingIteration | None]

        """
        if len(self._results) > 1:
            return self._results[-2]
        elif len(self._results) > 0:
            return self._results[-1]
        return None

    def command(self, simulation):
        """
        Assembles the command that would be run via command line.

        :param simulation: String name of simulation scala class
            Example drupal.UserSimulation
        :returns: String

        """
        return 'sh /opt/%s/bin/gatling.sh -s %s' % (self.config['gatling_dir'],
                                                    simulation)

    def env(self, users=None, duration=None, webheads=None):
        """
        Returns the environment for the process

        :param users: Number of users to push through gatling
        :param duration: Number of seconds over which to push the users
        :param webheads: Webheads to hit with users
        :returns: Dictionary of environment

        """
        users = users or self.users_start
        duration = duration or self.duration
        webheads = webheads or ','.join(self.get_webheads())
        return {
            'JAVA_OPTS': "-Dusers=%s -Dtime=%s -Dwebheads=%s" %
                         (users, duration, webheads)
        }

    def run(self):
        """
        Runs the Gatling workload
        Iterates until a stopping condition has been raised.

        """
        cmd = self.command()
        users = self.users_start
        step = self.users_step

        stdout_parser = GatlingStdoutParser()

        runners = self.minions_with_role(self.config['gatling_role'])
        timeout = max(2 * self.duration, 360)

        while(True):
            env = self.env(users=users)
            kwargs = {
                'timeout': timeout,
                'arg': (cmd,),
                'kwarg': {
                    'env': env,
                    'runas': self.config['gatling_user']
                }
            }

            # Execution response (still have to make another request to
            # get the simulation.log file contents)
            exe_resp = self.client.cmd(runners[0].id_, 'cmd.run_all', **kwargs)
            exe_resp = exe_resp.values()[0]
            retcode = exe_resp.get('retcode')
            stdout = exe_resp.get('stdout')
            stderr = exe_resp.get('stderr')
            stdout = cStringIO.StringIO(stdout)
            if stderr:
                # Do something with stderr if not empty or non none
                pass

            result = GatlingResult(users, self.duration, self.webheads)
            result.update({'retcode': retcode})
            result.update(stdout_parser.parse(stdout))
            print result

            # Attempt to get contents of simulation log
            kwargs = {
                'timeout': timeout,
                'arg': ('cat %s' % result.simulation_log,)
            }
            log_resp = self.client.cmd(runners[0].id_, 'cmd.run_all', **kwargs)
            log_resp = log_resp.values()[0]
            stdout = cStringIO.StringIO(log_resp.get('stdout'))
            stats = Stats()
            stats.update(stdout)
            result.update({'stats': stats})

            self._results.append(result)

            # Check process codes.
            # 0 = success
            # 2 = Gatling worked but at least one assertion failed
            if retcode not in [0, 2] or not result.success:
                # @TODO handle bad codes
                break
            users += step
