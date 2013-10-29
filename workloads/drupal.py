import cStringIO
import ConfigParser
import os
import subprocess

from common.workload import Workload
from common.gatling.iteration import Iteration
from common.gatling.stats import Stats

class DrupalWorkload(Workload):
    """
    Class that handles a drupal cloud workload.
    """

    def __init__(self):
        self._config()
        self._iterations = []

    def _config(self):
        """
        Loads necessary configuration values for this workload.
        """
        self._conf = {}

        parser = ConfigParser.ConfigParser()

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

        parser.read("config/drupal.ini")
        
        webheads = [webhead for key, webhead in parser.items("webheads")]
        self._conf.update(webheads=webheads)
        self._conf.update(duration=parser.get("run", "duration"))
        self._conf.update(users_start=parser.get("run", "users_start"))
        self._conf.update(users_step=parser.get("run", "users_step"))
        self._conf.update(gatling_path=parser.get("gatling", "path"))

    @property
    def users_start(self):
        return int(self._conf.get('users_start'))

    @property
    def users_step(self):
        return int(self._conf.get('users_step'))

    @property
    def duration(self):
        return int(self._conf.get('duration'))

    @property
    def webheads(self):
        return self._conf.get('webheads')

    @property
    def gatling_path(self):
        return self._conf.get('gatling_path')

    @property
    def best_iteration(self):
        return self._iterations[-2]

    def command(self):
        """
        Assembles the command that would be run via command line.

        :returns: String
        """
        script = os.path.join(self.gatling_path, 'bin/gatling.sh')
        return ['/bin/bash', script, '-s', 'drupal.UserSimulation']

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
        env['JAVA_OPTS'] =  "-Dusers=%s -Dtime=%s -Dwebheads=%s" % (
            users, duration, webheads)
        return env
                
    def run(self):
        """
        Runs the drupal workload
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

            if iteration.success == False:
                break

            users += step

        print "Last successful iteration"
        print self.best_iteration
        stats = Stats(self.best_iteration)
        print "Runs: %s" % len(stats.runs)
        print "Scenarios: %s" % len(stats.scenarios)
        print "Requests: %s" % len(stats.requests)
        print "Requests per second plot: %s" % stats.requests_per_second_plot
        print "Active sessions per second plot: %s" % stats.sessions_per_second_plot
        print "Response time plot: %s" % stats.response_times_plot
        

if __name__ == '__main__':
    load = DrupalWorkload()
    load.run()
