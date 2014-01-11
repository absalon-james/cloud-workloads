import os
import json
from ConfigParser import ConfigParser as BaseParser

class ConfigParser(BaseParser, object):

    def __init__(self, mode):
        super(ConfigParser, self).__init__()
        if mode == "salt":
            self.orig_read = self.read
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
              FIGURE OUT WHAT IS THROWN BY ORIG_READ WHEN FILE DOESN'T EXIST
        '''
        import salt.config

        #Get values from the file if available
        self.orig_read(config_file)

        #Overwrite file config with grain config
        caller = salt.client.Caller()
        grain_dict = caller.function('grains.items')

        workload_name = os.path.splitext(os.path.basename(config_file))[0]

        grain_config = grain_dict["workload_config"][workload_name]

        for section in grain_config:
            for key,val in grain_config[section].items():
                self.set(section, key, val)

        #Overwrite file and grain config with pillar config
        pillar_dict = caller.function('pillar.items')

        pillar_config = pillar_dict["workload_config"][workload_name]

        for section in pillar_config:
            for key,val in pillar_config[section].items():
                self.set(section, key, val)


