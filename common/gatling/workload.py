import cStringIO
#import ConfigParser
import os
import subprocess
import common.config_parser as ConfigParser

from common.workload import Workload as BaseWorkload
from iteration import Iteration
from stats import Stats


class Workload(BaseWorkload):
    """
    Class that handles a Gatling cloud workload.
    """

    def __init__(self, config_mode="flat_file"):
        self.config_mode = config_mode
        self._iterations = []
        self._config()

    def _config(self, conf_file):
        """
        Loads necessary configuration values for this workload.

        :param conf_file: String name of configuration file.
        """
        self._conf = {}

        parser = ConfigParser.ConfigParser(self.config_mode)

        # Default webheads
        parser.add_section("webheads")
        parser.set("webheads", "web1", "http://127.0.0.1")
        parser.set("webheads", "web2", "http://127.0.0.1")

        # Default run parameters
        parser.add_section("run")
        parser.set("run", "duration", "180")
        parser.set("run", "users_start", "500")
        parser.set("run", "users_step", "500")

        # Default gatling parameters
        parser.add_section("gatling")
        parser.set("gatling", "path", "~/gatling")

        parser.read(conf_file)

        webheads = [webhead for key, webhead in parser.items("webheads")]
        self._conf.update(webheads=webheads)
        self._conf.update(duration=parser.get("run", "duration"))
        self._conf.update(users_start=parser.get("run", "users_start"))
        self._conf.update(users_step=parser.get("run", "users_step"))
        self._conf.update(gatling_path=parser.get("gatling", "path"))

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
        return int(self._conf.get('users_start'))

    @property
    def users_step(self):
        """
        Returns the number of users per webhead to increase with
        every iteration.
        Taken from the config.

        :returns: Integer number of users per webhead to increase
        """
        return int(self._conf.get('users_step'))

    @property
    def duration(self):
        """
        Returns the number of seconds over which to run scenarios
        with the indicated number of users in seconds.
        Taken from the config.

        :returns:  Integer number of seconds
        """
        return int(self._conf.get('duration'))

    @property
    def webheads(self):
        """
        Returns the list of webheads.
        Taken from the config.

        :returns: List
        """
        return self._conf.get('webheads')

    @property
    def gatling_path(self):
        """
        Returns the location to gatling.
        Taken from the config.

        :returns: String
        """
        return self._conf.get('gatling_path')

    @property
    def best_iteration(self):
        """
        Returns the second to last iteration if there are more than one.
        The testing stops when an iteration fails.

        Returns the only iteration if only one.  The only iteration fails.

        Returns None otherwise (test probably hasn't been run yet.

        :returns: [GatlingIteration | None]
        """
        if len(self._iterations) > 1:
            return self._iterations[-2]
        elif len(self._iterations) > 0:
            return self._iterations[-1]
        return None

    def command(self, simulation):
        """
        Assembles the command that would be run via command line.

        :param simulation: String name of simulation scala class
            Example drupal.UserSimulation
        :returns: String
        """
        script = os.path.join(self.gatling_path, 'bin/gatling.sh')
        return ['/bin/bash', script, '-s', simulation]

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
        webheads = webheads or ','.join(self.webheads)
        env = dict(os.environ)
        env['JAVA_OPTS'] = "-Dusers=%s -Dtime=%s -Dwebheads=%s" % (
            users, duration, webheads)
        return env

    def run(self):
        """
        Runs the Gatling workload
        Iterates until a stopping condition has been raised.
        """

        cmd = self.command()
        users = self.users_start
        step = self.users_step

        while(True):
            env = self.env(users=users)
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env)
            output, err = process.communicate()
            output = cStringIO.StringIO(output)
            iteration = Iteration(users, self.duration, self.webheads, output)
            print iteration
            self._iterations.append(iteration)

            # Check process codes.
            # 0 = success
            # 2 = Gatling worked but at least one assertion failed
            if process.returncode not in [0, 2]:
                # Handle bad codes
                break
            if not iteration.success:
                break
            users += step

if __name__ == '__main__':
    Workload().run()
