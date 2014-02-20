import argparse
import os
import shutil
from common.config import YamlConfig
from common.view import View
from common.workload import Workload
from remote.client import Client
from remote.credentials import Pam
from remote.pool import MinionPool
from remote.event import EventStore, JobPoller
import traceback


class MissingWorkloadModuleError(Exception):
    """ Exception for when a workload module exists but not the class. """

    def __init__(self, workload):
        message = "Unable to locate a module for workload '%s'." % workload
        super(MissingWorkloadModuleError, self).__init__(message)


class MissingWorkloadClassError(Exception):
    """
    Exception for when the Workload class does not exist inside of a
    workload module.
    """

    def __init__(self, workload):
        message = "Unable to locate the Workload class within workloads.%s"
        message = message % workload
        super(MissingWorkloadClassError, self).__init__(message)


def load_workload_class(workload_name):
    # Loads a Workload class defined as
    # workloads.<workload_name>.Workload
    try:
        module = __import__('.'.join(['workloads', workload_name]), fromlist=[workload_name])
        return module.Workload
    except ImportError:
        raise MissingWorkloadModuleError(load)
    except AttributeError:
        raise MissingWorkloadClassError(load)


class Runner(object):
    """
    Runs all configured workloads and stitches output together into
    a combined view.
    """

    def __init__(self, config, credentials=None):
        """
        Inits the runner

        :param workloads: List of workload classes to run.
        
        """
        self.config = config
        self.credentials = credentials
        self.workloads = []
        self.primitives = None

    def run(self):
        """
        Runs workloads according to the config

        """
        event_store = EventStore()
        job_poller = JobPoller(event_store)

        # Set up the salt client
        client = Client(event_store, credentials=self.credentials)


        # Set up the minion pool
        pool_config = self.config.get_minion_pool()

        try:
            job_poller.start()
            minions = client.minions(pool_config['target'], pool_config['expr_form'])
            pool = MinionPool(minions)

            for name, workload_config in self.config.iter_workloads():
                class_name = workload_config.get('workload')
                workload_class = load_workload_class(class_name)
                workload = workload_class(client, pool, workload_config)

                print "-".ljust(80, '-')
                print ("---- Running workload %s " % workload.name).ljust(80, '-')
                print "-".ljust(80, '-')

                try:
                    workload.deploy()
                    workload.run()
                except Exception, e:
                    # @TODO Do something with the exception
                    print "Something happened when running workload: %s" % name
                    print e
                    print traceback.print_exc()
                    pass
                finally:
                    workload.undeploy()
        
                if (workload.is_primitive):
                    self.primitives = workload
                else:
                    self.workloads.append(workload)
        finally:
            print "Stopping the job poller"
            job_poller.signal_stop()
            job_poller.join()
            print "Job poller stopped"

    def view(self):
        """
        Creates a combined view containing all workload output.

        :returns: String
        """
        mapping = {
            'workloads': '<hr />'.join([w.view() for w in self.workloads]),
            'primitives': self.primitives.view() if self.primitives else ''
        }
        return View('main.html', mapping=mapping)


def parse_args():
    prog = "Cloud Workloads"
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument('config_file', help="Yaml configuration file describing cloud workloads.")
    parser.add_argument('output_dir', help="Output directory to place html, css, and javascript files.")
    parser.add_argument('--username', default=None, help="User for salt external authentication.")
    parser.add_argument('--password', default=None, help="Password for salt external authentication.")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    # Set up credentials
    if args.username is not None:
        credentials = Pam(args.username, args.password)
    else:
        credentials = None

    # Get the configuration
    config = YamlConfig(args.config_file)
    runner = Runner(config, credentials=credentials)
    runner.run()

    # try to create output directory with copy of assets
    assets_dir = os.path.dirname(__file__)
    assets_dir = os.path.abspath(os.path.join(assets_dir, 'assets'))
    try:
        shutil.copytree(assets_dir, args.output_dir)
    except OSError as e:
        print "Unable to create output directory: %s" % args.output_dir
        print e
        exit()

    output_file = os.path.join(args.output_dir, 'index.html')
    try:
        with open(output_file, 'w') as f:
            f.write(runner.view())
    except IOError:
        print "Unable to write results to %s." % output_file
        print e
