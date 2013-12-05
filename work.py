from common.view import View

class Runner(object):

    def __init__(self, workloads):
        """ Inits the runner """
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
        mapping = { 
            'workloads': ''.join([instance.view() for instance in self.instances]),
            'primitives': self.primitives.view() or ''
        }
        return View('main.html', mapping=mapping)

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
            raise Exception("Unable to locate workload '%s'." % load)
        except AttributeError:
            raise Exception("Unable to locate Workload class within module '%s'." % load)
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
