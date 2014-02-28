import argparse
import os
import shutil
from common.config import YamlConfig
from common.view import View
from remote.client import Client
from remote.credentials import Pam
from remote.pool import MinionPool
from remote.job import MultiJobException
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
        name = '.'.join(['workloads', workload_name])
        module = __import__(name, fromlist=[workload_name])
        return module.Workload
    except ImportError:
        raise MissingWorkloadModuleError(workload_name)
    except AttributeError:
        raise MissingWorkloadClassError(workload_name)


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
        Sets up the salt client, builds the minion pool and then
        runs workloads as described in the config.

        """
        # Set up the salt client
        client = Client(credentials=self.credentials)

        # Set up the minion pool
        pool_config = self.config.get_minion_pool()

        try:
            minions = client.minions(pool_config['target'],
                                     pool_config['expr_form'])
            pool = MinionPool(minions)

            for name, workload_config in self.config.iter_workloads():
                class_name = workload_config.get('workload')
                workload_class = load_workload_class(class_name)
                workload = workload_class(client, pool, workload_config)
                self.run_workload(workload)

                if (workload.is_primitive):
                    self.primitives = workload
                else:
                    self.workloads.append(workload)

        except KeyboardInterrupt:
            print ("Exit requested. !!Warning, there may be left over"
                   " cloud workloads on the minions.")
            exit()

        except Exception:
            print "Stopping due to exception"
            traceback.print_exc()

    def run_workload(self, workload):
        """
        Deploys, Runs, then Undeploys the workload

        @param workload - An object that subclasses workload

        """
        # Simple display output to help break up wall of text
        print "-".ljust(80, '-')
        title = ("---- Running workload %s " % workload.name)
        print title.ljust(80, '-')
        print "-".ljust(80, '-')

        try:
            workload.deploy()
            workload.run()

        # Catch salt job related exceptions
        except MultiJobException as e:
            print e

        finally:
            workload.undeploy()

    def view(self):
        """
        Creates a combined view containing all workload output.

        :returns: String
        """
        workload_views = '<hr />'.join([w.view() for w in self.workloads])
        if self.primitives:
            primitives_view = self.primitives.view()
        else:
            primitives_view = ''
        view = View(
            'main.html',
            workloads=workload_views,
            primitives=primitives_view
        )
        return view


def parse_args():
    prog = "Cloud Workloads"
    parser = argparse.ArgumentParser(prog=prog)

    help_ = "Yaml configuration file describing cloud workloads."
    parser.add_argument('config_file', help=help_)

    help_ = "Output directory to place html, css, and javascript files."
    parser.add_argument('output_dir', help=help_)

    help_ = "User for salt external authentication."
    parser.add_argument('--username', default=None, help=help_)

    help_ = "Password for salt external authentication."
    parser.add_argument('--password', default=None, help=help_)

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
    except IOError as e:
        print "Unable to write results to %s." % output_file
        print e
