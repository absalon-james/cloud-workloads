import yaml

# Descripts how to target requested minions for the minion pool.
# Default is everything
DEFAULT_MINION_POOL = {
    'target': '*',
    'expr_form': 'glob'
}


class YamlConfig(dict):
    """
    YamlConfig describing a sequence of workloads.

    """

    def __init__(self, filename):
        """
        Inits the config. Attemps to load specified yaml file.
        @param filename - String name of file to load

        """
        super(YamlConfig, self).__init__()
        with open(filename) as f:
            data = yaml.safe_load(f)
        self.update(data)

    def iter_workloads(self):
        """
        Generator for workloads described in this config.

        @yield Dictionary representing configs for a single workload.

        """
        for key, value in self.iteritems():
            try:
                if 'workload' in value:
                    yield key, value
            except TypeError:
                continue

    def get_minion_pool(self):
        """
        Returns the minion pool portion of the config.

        """
        return self.get('minion_pool', DEFAULT_MINION_POOL)
