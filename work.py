from common.view import View


class Runner(object):
    """
    Runs all configured workloads and stitches output together into
    a combined view.
    """

    def __init__(self, workloads):
        """
        Inits the runner

        :param workloads: List of workload classes to run.
        """
        self.workloads = workloads
        self.instances = []

    def run(self):
        """ Runs each workload """
        for workload in self.workloads:
            instance = workload()
            print "-".ljust(80, '-')
            print ("---- Running workload %s " % instance.name).ljust(80, '-')
            print "-".ljust(80, '-')
            instance.run()
        if (instance.is_primitive):
            self.primitives = instance
        else:
            self.instances.append(instance)

    def view(self):
        """
        Creates a combined view containing all workload output.

        :returns: String
        """
        mapping = {
            'workloads': '<hr />'.join([it.view() for it in self.instances]),
            'primitives': self.primitives.view() or ''
        }
        return View('main.html', mapping=mapping)


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


def load_workload_classes(loads):
    """
    Loads a list of workload classes.
    A workload class should be located in module inside of the
    workloads package.
    Example: the drupal workload should be workloads.drupal.Workload
    Example: the hadoop workload should be workloads.hadoop.Workload

    :returns: List of workload classes
    """
    workload_classes = []
    for load in loads:
        try:
            module = __import__('.'.join(['workloads', load]), fromlist=[load])
            workload_classes.append(module.Workload)
        except ImportError:
            raise MissingWorkloadModuleError(load)
        except AttributeError:
            raise MissingWorkloadClassError(load)
    return workload_classes

if __name__ == "__main__":
    import ConfigParser

    parser = ConfigParser.ConfigParser()
    parser.add_section("loads")
    parser.read("config/conf.ini")

    loads = [load for key, load in parser.items("loads")]

    classes = load_workload_classes(loads)
    runner = Runner(classes)
    runner.run()
    with open("index.html", "w") as outfile:
        outfile.write(runner.view())
