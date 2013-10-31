class Workload(object):
    """
    Class that handles a cloud workload.  A workload should consist
    of necessary tools to install, run, and parse output.

    Configuration should go in self.config
    Data collected during execution should go into self.data
    """

    def _config(self):
        """
        Should load any necessary configuration for the workload.
        Possibilities include webheads, db server addresses, number of
        clients, etc.
        """
        return {}

    def run(self):
        """Runs the workload"""
        return False

    def view(self):
        """
        Should return a string view of this workload.  The string should be
        valid html that can be dumped with other html.

        :returns: String html representation of workload output
        """

    @property
    def name(self):
        """
        Returns the name of the workload.

        :returns: String name of the workload
        """
        return "!!! Name not set !!!"
