import ConfigParser
import cStringIO
import os
import subprocess
import time
from common.workload import Workload as BaseWorkload
from common.view import View

from operator import attrgetter
import pprint

class TeraResult(dict):

    tags = ['Launched reduce tasks', 'Launched map tasks',
            'HDFS_BYTES_READ', 'HDFS_BYTES_WRITTEN',
            'Reduce output records', 'Map output records']

    def __init__(self, resp, start, end):
        super(TeraResult, self).__init__()
        self.update({
            'start': start,
            'end': end,
            'duration': end - start
        })
        self.update(resp)
        output = "\n".join([self.get('stdout', ''), self.get('stderr', '')])
        output = cStringIO.StringIO(output)
        self._parse(output)

    def _parse(self, output):
        for line in output:
            line = line.rstrip()
            tokens = line.split(None, 4)
            if len(tokens) > 4:
                keyvalue = tokens[-1].split('=')
                if len(keyvalue) == 2:
                    key, value = keyvalue
                    self[key] = value
        

class Workload(BaseWorkload):
    """
    Class that handles a MySQL workload.
    """

    DEFAULT_STATES = {
        'hadoop_master': ['hadoop.hdfs', 'hadoop.mapred'],
        'hadoop_slave': ['hadoop.hdfs', 'hadoop.mapred']
    }

    DEFAULT_ANTI_STATES = {
        'hadoop_master': ['hadoop.antihadoop'],
        'hadoop_slave': ['hadoop.antihadoop']
    }

    DEFAULT_CONFIG = {
        'hadoop_master_role': 'hadoop_master',
        'hadoop_path': '/usr/lib/hadoop/',
        'hadoop_example': 'hadoop-examples-1.2.1.jar',
        'hadoop_user': 'hdfs',
        'terasort_data_path': '/teragen',
        'terasort_size': 500000, # number of 100 byte lines to sort
    }

    def __init__(self, client, pool, config):
        super(Workload, self).__init__(client, pool, config)
        self.result = {}

    @property
    def name(self):
        """
        Returns the name of the workload.

        :returns: String name of the workload
        """
        return "Hadoop"

    def example_jar(self):
        return os.path.join(self.config['hadoop_path'], self.config['hadoop_example'])

    def hadoop_bin(self):
        return os.path.join(self.config['hadoop_path'], 'bin/hadoop')

    def teragen_command(self):
        """
        """
        return "%s jar %s teragen %s %s/unsorted" % (
            self.hadoop_bin(),
            self.example_jar(),
            self.config['terasort_size'],
            self.config['terasort_data_path']
        )

    def terasort_command(self):
        """
        """
        return "%s jar %s terasort %s/unsorted %s/sorted" % (
            self.hadoop_bin(),
            self.example_jar(),
            self.config['terasort_data_path'],
            self.config['terasort_data_path']
        )

    def run(self):
        """Runs the workload"""

        pp = pprint.PrettyPrinter(indent=4)
        runner = self.minions_with_role(self.config['hadoop_master_role'])[0]

        teragen_cmd = self.teragen_command()
        print "running: ", teragen_cmd
        kwargs = {
            'kwarg': {
                'runas': self.config['hadoop_user']               
            },
            'arg': (teragen_cmd,),
            'timeout': 480 
        }
        start = time.time()
        teragen_resp = self.client.cmd(runner.id_, 'cmd.run_all', **kwargs).values()[0]
        end = time.time()

        print "Tergen response:"
        #print "Retcode: %s" % teragen_resp['retcode']
        #print "Stdout: ", teragen_resp.get('stdout', 'woops')
        #print "Stderr: ", teragen_resp.get('stderr', 'woops')
        self.result['teragen'] = TeraResult(teragen_resp, start, end)

        terasort_cmd = self.terasort_command()
        print "running: ", terasort_cmd
        kwargs.update({
            'arg': (terasort_cmd,)
        })
        start = time.time()
        terasort_resp = self.client.cmd(runner.id_, 'cmd.run_all', **kwargs).values()[0]
        end = time.time()
        print "Terasort response:"
        #print "Retcode: %s" % terasort_resp['retcode']
        #print "Stdout: ", terasort_resp.get('stdout', 'woops')
        #print "Stderr: ", terasort_resp.get('stderr', 'woops')
        self.result['terasort'] = TeraResult(terasort_resp, start, end)
    
    def view(self):
        """
        Should return a string view of this workload.  The string should be
        valid html that can be dumped with other html.

        :returns: String html representation of workload output
        """

        return View('hadoop.html', {
            'numrecords': self.result['teragen'].get('Map output records', '??'),
            'teragen_duration': "%.2f" % self.result['teragen'].get('duration', 0),
            'teragen_map_tasks': self.result['teragen'].get('Launched map tasks', 0),
            'terasort_duration': "%.2f" % self.result['terasort'].get('duration', 0),
            'terasort_map_tasks': self.result['terasort'].get('Launched map tasks', 0),
            'terasort_reduce_tasks': self.result['terasort'].get('Launched reduce tasks', 0),
            
        })

if __name__ == "__main__":
    load = Workload()
    load.run()
