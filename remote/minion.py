class Minion(object):
    """
    Models a salt minion and provides convenience methods
    or accessing important grains
    """

    def __init__(self, grains_dict):
        """
        Takes in a dict of the minion's grains.

        @param grains_dict - Dictionary of grains info

        """
        self.data = grains_dict
    
    def __getitem__(self, key, default=None):
        """
        Overrides the default getitem so that a path can be specified.
        Example: ['interface:eth0'] instead of having
        to do ['interface']['eth0']

        @param key - String key/path that is colon delimited
        @param default - Default value to return
        """
        keys = key.split(':')
        value = self.data
        while len(keys) > 0:
            key = keys.pop(0)
            try:
                value = value[key]
            except TypeError:
                return default
            except KeyError:
                return default
        return value

    def update(self, update):
        """
        Updates the dict

        @param update - Dict containing updates
        """
        self.data.update(update)

    @property
    def id_(self):
        return self['id']

    @property
    def cpu_model(self):
        return self['cpu_model']

    @property
    def cpu_arch(self):
        return self['cpuarch']

    @property
    def num_cpus(self):
        return self['num_cpus']

    @property
    def memory(self):
        return self['mem_total']

    @property
    def os(self):
        return self['os']
 
    @property
    def osarch(self):
        return self['osarch']

    @property
    def osrelease(self):
        return self['osrelease']

    @property
    def interfaces(self):
        return self['interfaces']

    def interface(interface):
        return self['interface:%s' % interface]

    @property
    def roles(self):
        return self['roles']
