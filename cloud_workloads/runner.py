import collections
import traceback
from remote.client import Client
from remote.pool import MinionPool
from remote.job import MultiJobException


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
        name = '.'.join(['cloud_workloads.workloads', workload_name])
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

    def __init__(self, config):
        """
        Inits the runner

        :param workloads: List of workload classes to run.

        """
        self.config = config
        self.views = collections.OrderedDict()
        self.workloads = []
        self.primitives_view = None

    def run(self):
        """
        Sets up the salt client, builds the minion pool and then
        runs workloads as described in the config.

        """
        # Set up the salt client
        print "Setting up the client"
        client = Client()

        # Set up the minion pool
        pool_config = self.config.get_minion_pool()

        try:
            print "Setting up the pool"
            minions = client.minions(pool_config['target'],
                                     pool_config['expr_form'],
                                     timeout=5)
            pool = MinionPool(minions)

            for name, workload_config in self.config.iter_workloads():
                class_name = workload_config.get('workload')
                workload_class = load_workload_class(class_name)
                workload = workload_class(client, pool, workload_config)
                self.run_workload(workload)

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
            print "Multi job problem found. need to save the trace"
            workload.data_dict['exception_trace'] = traceback.format_exc()
            print e

        finally:
            workload.undeploy()

        self.workloads.append(workload)
