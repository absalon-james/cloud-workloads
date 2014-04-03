import cStringIO
import os
import subprocess
import time
from cloud_workloads.common.workload import Workload as BaseWorkload


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
        'terasort_size': 500000,
        'formula_dir': '/srv/salt/hadoop'
    }

    DEPLOY_SEQUENCE = [
        {'state': 'hadoop.hdfs',
         'next': {'state': 'hadoop.mapred'}}
    ]

    UNDEPLOY_SEQUENCE = [
        {'state': 'hadoop.antihadoop'}
    ]

    MINION_GRAPH_EDGE_MAP = {
        'hadoop_master': ['hadoop_slave']
    }

    def __init__(self, client, pool, config):
        """
        Workload constructor

        """
        super(Workload, self).__init__(client, pool, config)
        self.result = {}
        self.generate_keys()

    def generate_keys(self):
        """
        The hadoop salt formula includes a script called
        'generate_keypairs.sh' that generates public and private keys
        for yarn, mapred, and hdfs. This method executes that script
        in that script's directory. The script will create keys if they
        do not already exist.

        """
        print "Generating keys"
        oldcwd = os.getcwd()
        key_script_dir = os.path.join(self.config['formula_dir'], 'files')
        try:
            os.chdir(key_script_dir)
            subprocess.check_call(['sh', 'generate_keypairs.sh'])
        finally:
            os.chdir(oldcwd)

    @property
    def name(self):
        """
        Returns the name of the workload.

        :returns: String name of the workload
        """
        return "Hadoop"

    def example_jar(self):
        """
        Returns the path to the example jar.

        @returns - String

        """
        return os.path.join(self.config['hadoop_path'],
                            self.config['hadoop_example'])

    def hadoop_bin(self):
        """
        Returns the path to the hadoop bin

        @returns - String

        """
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

        runner = self.minions_with_role(self.config['hadoop_master_role'])[0]

        teragen_cmd = self.teragen_command()
        print "running: ", teragen_cmd
        kwargs = {
            'kwarg': {
                'runas': self.config['hadoop_user']
            },
            'arg': (teragen_cmd,),
            'timeout': 3600
        }
        start = time.time()
        teragen_resp = self.client.cmd(runner.id_, 'cmd.run_all', **kwargs)
        teragen_resp = teragen_resp.values()[0]
        end = time.time()

        #print "Tergen response:"
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
        terasort_resp = self.client.cmd(runner.id_, 'cmd.run_all', **kwargs)
        terasort_resp = terasort_resp.values()[0]
        end = time.time()
        #print "Terasort response:"
        #print "Retcode: %s" % terasort_resp['retcode']
        #print "Stdout: ", terasort_resp.get('stdout', 'woops')
        #print "Stderr: ", terasort_resp.get('stderr', 'woops')
        self.result['terasort'] = TeraResult(terasort_resp, start, end)

    def data(self):
        """
        Should return a string view of this workload.  The string should be
        valid html that can be dumped with other html.

        :returns: String html representation of workload output
        """

        if self.data_dict.get('exception_trace'):
            return self.data_dict

        result = self.result

        teragen_duration = result['teragen'].get('duration', 0)
        teragen_duration = round(teragen_duration, 2)
        terasort_duration = result['terasort'].get('duration', 0)
        terasort_duration = round(terasort_duration, 2)
        total_time = teragen_duration + terasort_duration
        if total_time > 0:
            teragen_percent = round((teragen_duration / total_time) * 100, 2)
            terasort_percent = round((terasort_duration / total_time) * 100, 2)
        else:
            teragen_percent = 0
            terasort_percent = 0

        datapoints = [
            {'y': teragen_duration,
             'indexLabel': "%s%%" % teragen_percent,
             'name': "Time generating data"},
            {'y': terasort_duration,
             'indexLabel': "%s%%" % terasort_percent,
             'name': "Time sorting data"}
        ]

        numrecords = result['teragen'].get('Map output records', '??')
        teragen_map_tasks = result['teragen'].get('Launched map tasks', 0)
        terasort_map_tasks = result['terasort'].get('Launched map tasks', 0)
        terasort_reduce_tasks = \
            result['terasort'].get('Launched reduce tasks', 0)

        self.data_dict.update({
            'numrecords': numrecords,
            'teragen_duration': teragen_duration,
            'teragen_map_tasks': teragen_map_tasks,
            'terasort_duration': terasort_duration,
            'terasort_map_tasks': terasort_map_tasks,
            'terasort_reduce_tasks': terasort_reduce_tasks,
            'terasort_data_points': datapoints
        })
        return self.data_dict
