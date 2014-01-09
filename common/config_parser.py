from ConfigParser import ConfigParser as BaseParser
import os
import json

class ConfigParser(BaseParser, object):

    def __init__(self, mode):
        super(ConfigParser, self).__init__()
        if mode == "salt":
            self.read = self.read_salt

    def read_salt(self, config_file):
        '''
        Reads config values from the salt grains/pillars.
        This must be run on the minion as it uses salt.client.Caller().
        If the mode is not salt this method isn't applied.

        :param conf_file: String name of configuration file.
                          This is not used here but needs to be included
                          for when config_mode is flat_file

        TODO: decide what things should be done in grains vs pillars
        '''
        import salt.config

        caller = salt.client.Caller()
        grain_dict = caller.function('grains.items')

        workload_config = grain_dict["workload_config"]

        for section in workload_config:
            for key,val in workload_config[section].items():
                self.set(section, key, val)

