import cStringIO
import os
from collections import OrderedDict
from cloud_workloads.common.primitives.bench_analyzer import bench_analyzer
from cloud_workloads.common.primitives.parser import \
    io_parser, cpu_parser, network_parser
from cloud_workloads.common.view import View
from cloud_workloads.common.workload import Workload as BaseWorkload


class Workload(BaseWorkload):
    """
    Class that handles a Primitive cloud workload.
    """

    DEFAULT_STATES = {
        'primitives': ['primitives'],
        'primitives_target': ['primitives']
    }

    DEFAULT_ANTI_STATES = {
        'primitives': ['primitives.anti'],
        'primitives_target': ['primitives.anti']
    }

    DEFAULT_CONFIG = {
        'runner_role': 'primitives',
        'target_role': 'primitives_target',
        'primitives_dir': '/opt/primitives',

        'cpu_tests': [
            'dhry2reg',
            'whetstone-double',
            'syscall',
            'pipe',
            #'context1', # Having trouble running this one through salt
            'spawn',
            'execl'
        ],
        'cpu_dir': 'UnixBench',
        'cpu_iterations_per_test': 10,

        'io_tests': [
            'randomrw.f',
            #'singlestreamreaddirect.f',
            'singlestreamread.f',
            'singlestreamwritedirect.f',
            'singlestreamwrite.f'
        ],
        'io_dir': 'filebench-1.4.9.1',

        'network_dir': 'iperf-2.0.5'
    }

    DEPLOY_SEQUENCE = [
        {'state': 'primitives'}
    ]

    UNDEPLOY_SEQUENCE = [
        {'state': 'primitives.anti'}
    ]

    MINION_GRAPH_EDGE_MAP = {
        'primitives': ['primitives_target']
    }

    def __init__(self, client, pool, config):
        super(Workload, self).__init__(client, pool, config)
        self.is_primitive = True
        self._iterations = []

    @property
    def name(self):
        """
        Returns name of the workload.

        :returns: String name of the workload
        """
        return "Primitives"

    @property
    def primitives_dir(self):
        """
        Returns the location of primtive benchmarks.
        Taken from the config.

        :returns: String of directory name
        """
        return self.config.get('primitives_dir')

    @property
    def cpu_tests(self):
        """
        Returns the name list of CPU tests to run.
        Taken from the config.

        :returns: list of test names to include
        """
        return self.config.get('cpu_tests')

    @property
    def cpu_directory(self):
        """
        Returns the location of CPU bench.
        Taken from the config.

        :returns: String of directory name
        """
        return self.config.get('cpu_dir')

    @property
    def cpu_iterations_per_test(self):
        """
        Returns the number of iterations for tests.
        Slow tests iterate 1/3 of the times.
        Taken from the config.

        :returns: Integer number of iterations per test
        """
        return int(self.config.get('cpu_iterations_per_test'))

    @property
    def cpu_parallel_copies(self):
        """
        Returns the number of parallel copies to run for each test.
        Taken from the config.

        :returns:  Integer number of parallel test copies
        """
        return int(self.config.get('cpu_parallel_copies'))

    @property
    def io_tests(self):
        """
        Returns the name list of IO tests to run.
        Taken from the config.

        :returns: list of test names to include
        """
        return self.config.get('io_tests')

    @property
    def io_dir(self):
        """
        Returns the location of IO bench.
        Taken from the config.

        :returns: String of directory name
        """
        return self.config.get('io_dir')

    def cpu_command(self):
        """
        Assembles the command that would be run via command line.

        :returns: String
        """
        cmd = './Run %s -i %s' % (
            ' '.join(self.config['cpu_tests']),
            self.config['cpu_iterations_per_test']
        )

        cwd = os.path.join(self.config['primitives_dir'],
                           self.config['cpu_dir'])

        kwargs = {
            'timeout': 3600,
            'arg': (cmd,),
            'kwarg': {
                'cwd': cwd
            }
        }
        return kwargs

    def io_commands(self):
        """
        Assembles the command that would be run via command line.

        :returns: String
        ./filebench -f workloads/randomrw.f
        """
        empty_cmd = "%s -f %s"
        kwargss = []
        script = os.path.join(self.primitives_dir, self.io_dir, 'filebench')
        io_workload_dir = os.path.join(self.primitives_dir, self.io_dir,
                                       "workloads")
        for test in self.io_tests:
            test_file = os.path.join(io_workload_dir, test)
            kwargss.append({
                'arg': (empty_cmd % (script, test_file),),
                'timeout': 3600
            })
        return kwargss

    def network_commands(self):
        """
        Assembles the command that would be run via command line.

        :returns: String
        """
        target = self.minions_with_role(self.config['target_role'])
        ips_dict = self.client.get_ips(target, interface='private')
        remote_host = ips_dict.values()[0][0]

        return {
            'remote': {'arg': ('iperf -s',),
                       'timeout': 360},
            'local':  {'arg': ('iperf -c %s -d' % remote_host,),
                       'timeout': 360}
        }

    def run_cpu(self):

        #--------------------CPU CMD--------------------
        runner = self.minions_with_role(self.config['runner_role'])[0]
        cpu_kwargs = self.cpu_command()
        cpu_resp = self.client.cmd(runner.id_, 'cmd.run_all', **cpu_kwargs)
        cpu_resp = cpu_resp.values()[0]

        # getting data is a two step process
        # Step 1 is parse the file name out of stdout
        cpu_data = cpu_parser(cStringIO.StringIO(cpu_resp['stdout']))

        # Step 2 is to get the contents of that file
        kwargs = {
            'arg': ('cat %s' % cpu_data['json_data_file'],)
        }
        data_resp = self.client.cmd(runner.id_, 'cmd.run_all', **kwargs)
        data_resp = data_resp.values()[0]

        print "Cpu stdout"
        print data_resp['stdout']
        cpu_data.update_with_json(data_resp['stdout'])


        #take output and analyze it. Basically take weighted averages of
        #results
        ub_info = OrderedDict()
        ub_info['run_1'] = {
            "normalizer": 1000,
            "weight": 1
        }
        ub_info['run_2'] = {
            "normalizer": 3000,
            "weight": 1
        }

        ub_create_score_dict = \
            lambda x: {"run_%d" % test_run: x[test_run]["index"]["system"]
                       for test_run in [1, 2]}
        self.cpu_analyzer = bench_analyzer(ub_info,
                                           ub_create_score_dict,
                                           json_data=cpu_data)

    def run_io(self):
        runner = self.minions_with_role(self.config['runner_role'])[0]

        #Grab list of commands we're going to run and initialize the io parser
        kwargss = self.io_commands()
        fb_data = io_parser()

        #run commands and add output to parser as we go
        for kwargs in kwargss:
            resp = self.client.cmd(runner.id_, 'cmd.run_all', **kwargs)
            resp = resp.values()[0]
            output = cStringIO.StringIO(resp['stdout'])
            print "\n\nStd out for %s" % kwargs
            print resp['stdout']
            fb_data.parse(kwargs['arg'][0], output)

        #analyze results. as before this is essentially a weighted average
        fb_info = OrderedDict()
        fb_info['randomrw.f'] = {
            "normalizer": 120.0,
            "weight": 1,
            "units": "Mbits/sec"
        }
        #fb_info['singlestreamreaddirect.f'] = {
        #    "normalizer": 120.0,
        #    "weight": 1,
        #    "units": "Mbits/sec"
        #}
        fb_info['singlestreamread.f'] = {
            "normalizer": 1000.0,
            "weight": 1,
            "units": "Mbits/sec"
        }
        fb_info['singlestreamwritedirect.f'] = {
            "normalizer": 1000.0,
            "weight": 1,
            "units": "Mbits/sec"
        }
        fb_info['singlestreamwrite.f'] = {
            "normalizer": 1000.0,
            "weight": 1,
            "units": "Mbits/sec"
        }
        fb_create_score_dict = lambda x: {key: val
                                          for key, val in x.iteritems()}
        self.io_analyzer = bench_analyzer(fb_info,
                                          fb_create_score_dict,
                                          json_data=fb_data)

    def run_network(self):

        #Get the local and remote commands that we'll need to run
        network_kwargss = self.network_commands()

        # Start the listening iperf server
        remote_runner = self.minions_with_role(self.config['target_role'])[0]
        remote_kwargs = network_kwargss['remote']
        self.client.job(remote_runner.id_, 'cmd.run_all', **remote_kwargs)

        runner = self.minions_with_role(self.config['runner_role'])[0]
        runner_kwargs = network_kwargss['local']
        runner_resp = self.client.cmd(runner.id_,
                                      'cmd.run_all',
                                      **runner_kwargs)
        runner_resp = runner_resp.values()[0]
        print "\n\nStdout for nework"
        print runner_resp['stdout']
        network_data = network_parser(
            cStringIO.StringIO(runner_resp['stdout'])
        )

        network_info = OrderedDict()
        network_info['conn_0'] = {
            "normalizer": 1024.0,
            "weight": 1,
            "units": 'Mbits/sec'
        }
        network_info['conn_1'] = {
            "normalizer": 1024.0,
            "weight": 1,
            "units": 'Mbits/sec'
        }

        network_create_score_dict = \
            lambda x: {"conn_%s" % num:
                       x["connections"][conn]["bandwidth_mb/sec"]
                       for conn, num in zip(x["connections"],
                                            range(len(x["connections"])))
                       }
        self.network_analyzer = bench_analyzer(network_info,
                                               network_create_score_dict,
                                               json_data=network_data)

    def run(self):
        """
        Runs the Primitive workload
        """

        self.run_cpu()
        self.run_io()
        self.run_network()

        #--------------------Overall Score------------------
        #Get scores for each type of test and put them together
        #as the overall score
        overall_info = OrderedDict()
        overall_info['unixbench'] = {
            "normalizer": 100.0,
            "weight": 1
        }
        overall_info['filebench'] = {
            "normalizer": 100.0,
            "weight": 1
        }
        overall_info['iperf'] = {
            "normalizer": 100.0,
            "weight": 1
        }

        overall_create_score_dict = lambda x: {key: val
                                               for key, val in x.iteritems()}
        overall_data = {
            "unixbench": self.cpu_analyzer.overall_score,
            "filebench": self.io_analyzer.overall_score,
            "iperf": self.network_analyzer.overall_score
        }
        self.overall_analyzer = bench_analyzer(overall_info,
                                               overall_create_score_dict,
                                               json_data=overall_data)

    def view(self):
        """
        Returns an html formatted string.

        @return - String
        """
        self.view_dict.update({
            'overall_score': int(self.overall_analyzer.overall_score),
            'cpu_score': int(self.cpu_analyzer.overall_score),
            'io_score': int(self.io_analyzer.overall_score),
            'network_score': int(self.network_analyzer.overall_score),
            'overall_scores': self.overall_analyzer.score_info,
            'cpu_scores': self.cpu_analyzer.score_info,
            'io_scores': self.io_analyzer.score_info,
            'network_scores': self.network_analyzer.score_info
        })
        return View('primitives.html', **(self.view_dict))
