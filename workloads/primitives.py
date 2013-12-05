import ConfigParser
import cStringIO
import json
import os
import parse
import paramiko
import subprocess
import time

from common.primitives.bench_analyzer import bench_analyzer
from common.primitives.parser import io_parser
from common.view import View
from common.workload import Workload as BaseWorkload


class Workload(BaseWorkload):
    """
    Class that handles a Primitive cloud workload.
    """
    unixbench_json_file_tag = "JSON_FILE:"
    filebench_summary_tag = "IO Summary:"

    def __init__(self):
	self.is_primitive = True
        self._iterations = []
        self._config()

    def _config(self):
        """
        Loads necessary configuration values for this workload.

        :param conf_file: String name of configuration file.
        """
        self._conf = {}
        conf_file = 'config/primitives.ini'

        parser = ConfigParser.ConfigParser()

        parser.add_section("Primitives")
        parser.set("Primitives", "bench_location", "~")

        # Default CPU parameters
        parser.add_section("CPU")
        parser.set("CPU", "directory", "UnixBench")
        parser.set("CPU", "tests_to_run", "dhry2reg")
        parser.set("CPU", "iterations_per_test", "10") #EX. ./Run -i 10
        parser.set("CPU", "parallel_copies", "1") #EX. ./Run -c 1

        # Default IO parameters
        parser.add_section("IO")
        parser.set("IO", "directory", "filebench-1.4.9.1")
        parser.set("IO", "tests_to_run", "randomrw.f")

        # Default Network parameters
        parser.add_section("Network")
        parser.set("Network", "directory", "iperf-2.0.5")
        parser.set("Network", "remote_host", "127.0.0.1")
        parser.set("Network", "remote_user", "user")
        parser.set("Network", "remote_cred_type", "remote_password")
        parser.set("Network", "remote_password", "password")
        parser.set("Network", "remote_key", "~/.ssh/id_rsa")

        parser.read(conf_file)
        
        CPU_tests = parser.get("CPU", "tests_to_run").split(",")
        IO_tests = parser.get("IO", "tests_to_run").split(",")

        self._conf.update(Primitives_bench_location=parser.get("Primitives", "bench_location"))
        
        self._conf.update(CPU_tests=CPU_tests)
        self._conf.update(CPU_directory=parser.get("CPU", "directory"))
        self._conf.update(CPU_iterations_per_test=parser.get("CPU", "iterations_per_test"))
        self._conf.update(CPU_parallel_copies=parser.get("CPU", "parallel_copies"))

        self._conf.update(IO_tests=IO_tests)
        self._conf.update(IO_directory=parser.get("IO", "directory"))

        self._conf.update(Network_remote_host=parser.get("Network", "remote_host"))
        self._conf.update(Network_remote_user=parser.get("Network", "remote_user"))
        self._conf.update(Network_remote_cred_type=parser.get("Network", "remote_cred_type"))
        self._conf.update(Network_remote_password=parser.get("Network", "remote_password"))
        self._conf.update(Network_remote_key=parser.get("Network", "remote_key"))

    @property
    def name(self):
        """
        Returns name of the workload.
    
        :returns: String name of the workload
        """
        return "Primitives"

    @property
    def Primitives_bench_location(self):
        """
        Returns the location of primtive benchmarks.
        Taken from the config.

        :returns: String of directory name
        """
        return self._conf.get('Primitives_bench_location')

    @property
    def CPU_tests(self):
        """
        Returns the name list of CPU tests to run.
        Taken from the config.

        :returns: list of test names to include
        """
        return self._conf.get('CPU_tests')

    @property
    def CPU_directory(self):
        """
        Returns the location of CPU bench.
        Taken from the config.

        :returns: String of directory name
        """
        return self._conf.get('CPU_directory')

    @property
    def CPU_iterations_per_test(self):
        """
        Returns the number of iterations for tests.
        Slow tests iterate 1/3 of the times.
        Taken from the config.

        :returns: Integer number of iterations per test
        """
        return int(self._conf.get('CPU_iterations_per_test'))

    @property
    def CPU_parallel_copies(self):
        """
        Returns the number of parallel copies to run for each test.
        Taken from the config.

        :returns:  Integer number of parallel test copies
        """
        return int(self._conf.get('CPU_parallel_copies'))

    @property
    def IO_tests(self):
        """
        Returns the name list of IO tests to run.
        Taken from the config.

        :returns: list of test names to include
        """
        return self._conf.get('IO_tests')

    @property
    def IO_directory(self):
        """
        Returns the location of IO bench.
        Taken from the config.

        :returns: String of directory name
        """
        return self._conf.get('IO_directory')

    @property
    def Network_remote_host(self):
        """
        Returns the ip or hostname of the remote host.
        Taken from the config.

        :returns: String
        """
        return self._conf.get('Network_remote_host')

    @property
    def Network_remote_user(self):
        """
        Returns the name of the user for the remote host.
        Taken from the config.

        :returns: String
        """
        return self._conf.get('Network_remote_user')

    @property
    def Network_remote_cred_type(self):
        """
        Returns the type of credentials to be used
        Taken from the config.

        :returns: String
        """
        return self._conf.get('Network_remote_cred_type')

    @property
    def Network_remote_password(self):
        """
        Returns the password for the remote host/user
        Taken from the config.

        :returns: String
        """
        return self._conf.get('Network_remote_password')

    @property
    def Network_remote_key(self):
        """
        Returns the location of the ssh key with access to remote server.
        Taken from the config.

        :returns: String
        """
        return self._conf.get('Network_remote_key')

    def CPU_command(self):
        """
        Assembles the command that would be run via command line.

        :returns: String
        """
        script = './Run'
        tests = self.CPU_tests
        return [script] + tests + ['-c', str(self.CPU_parallel_copies), '-i', str(self.CPU_iterations_per_test)]

    def IO_commands(self):
        """
        Assembles the command that would be run via command line.

        :returns: String
        ./filebench -f workloads/randomrw.f
        """
        script = os.path.join(self.Primitives_bench_location, self.IO_directory, 'filebench')
        tests = self.IO_tests
        commands = []

        for test in tests:
            test_file = os.path.join(self.Primitives_bench_location, self.IO_directory, "workloads", test)
            commands.append([script, '-f', test_file])

        return commands

    def Network_commands(self):
        """
        Assembles the command that would be run via command line.

        :returns: String
        """
        script = 'iperf'
        return {"remote": [script, '-s'], "local": [script, '-c', self.Network_remote_host, "-d"]}

    def run_command(self, cmd):
	"
	Runs the given command and provides the output
	
	:returns: cStringIO object
	"
	process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        output, err = process.communicate()
        return cStringIO.StringIO(output)

    def run(self):
        """
        Runs the Primitive workload
        """
    	
        #--------------------CPU CMD--------------------
        orig_dir = os.getcwd()
    	os.chdir(os.path.join(self.Primitives_bench_location, self.CPU_directory))
        cmd = self.CPU_command()
	output = self.run_command(cmd)
    	for line in output:
    		if line.startswith(self.unixbench_json_file_tag):
    			json_data_file = line.split()[1]  
        os.chdir(orig_dir)

    	if json_data_file is None:
    		raise Error("unable to locate unix bench file")
    	ub_info = {"dhry2reg": 
                    {
                        "normalizer": 119342529.0,
                        "weight": 1
                    }
                   }
        ub_create_score_dict = lambda x: {test_name: x[test_name]["score"] for test_name in x["list"]}
        self.cpu_analyzer = bench_analyzer(ub_info, ub_create_score_dict, file_name=json_data_file)
        #------------------------------------------------

        #--------------------IO CMD------------------------
        cmds = self.IO_commands()
        fb_parser = io_parser()

        fb_data = {}
        for cmd in cmds:
	    output = self.run_command(cmd)
            for line in output:
                if self.filebench_summary_tag in line:
		    mbps = line.split(", ")[-3].replace("mb/s", "")
		    test_name = cmd[-1].split("/")[-1]
		    fb_data[test_name] = float(mbps)
	fb_info = { "randomrw.f": { 
				    "normalizer": 60.0,
				    "weight": 1
			    }
		  }
        fb_create_score_dict = lambda x: {key:val for key,val in x.iteritems()}
        self.io_analyzer = bench_analyzer(fb_info, fb_create_score_dict, json_data=fb_data)
        #--------------------------------------------------

        #--------------------NET CMD------------------------
	cmds = self.Network_commands()
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	ssh.connect(self.Network_remote_host, username=self.Network_remote_user, password=self.Network_remote_password)
	ssh.exec_command(" ".join(cmds["remote"]))
	time.sleep(5)

	output = self.run_command(cmds["local"])
	iperf_data = {"window_sizes": [], "connections": {}}
        for line in output:
	    words = line.split()
	    if (words[0] == "TCP"):
		iperf_data["window_sizes"].append(words[3])
	    elif(words[0] == "[" and words[1] != "ID]"):
		conn_num = words[1].replace("]", "")
		if (words[2] == "local"):
		    iperf_data["connections"][conn_num] = {"local_ip": words[3], "local_port": words[5], "remote_ip": words[8], "remote_port": words[10]}
		else:
		    interval_list = words[2].split("-")
		    iperf_data["connections"][conn_num]["interval_start"] = interval_list[0]
		    iperf_data["connections"][conn_num]["interval_stop"] = interval_list[1]
		    iperf_data["connections"][conn_num]["transfer_mb"] = words[4]
		    iperf_data["connections"][conn_num]["bandwidth_mb/sec"] = words[6]

	iperf_info = { "conn_0": { "normalizer": 1024.0,
				   "weight": 1
				 },
		       "conn_1": { "normalizer": 1024.0,
			  	   "weight": 1
			  	 }
		     }
	iperf_create_score_dict = lambda x: {"conn_%s" % num: x["connections"][conn]["bandwidth_mb/sec"] for conn, num in zip(x["connections"], range(len(x["connections"])) )}
	self.network_analyzer = bench_analyzer(iperf_info, iperf_create_score_dict, json_data=iperf_data)
        #--------------------------------------------------

	#--------------------Overall Score------------------
	overall_info = { "unixbench": { "normalizer": 100.0,
					"weight": 1
				      },
			 "filebench": { "normalizer": 100.0,
			   		"weight": 1
			   	      },
			 "iperf":     { "normalizer": 100.0,
			   		"weight": 1
			   	      }
			}
	overall_create_score_dict = lambda x: {key:val for key,val in x.iteritems()}
	overall_data = { "unixbench": self.cpu_analyzer.json_data["overall_score"], 
			 "filebench": self.io_analyzer.json_data["overall_score"],
			 "iperf": self.network_analyzer.json_data["overall_score"]
		       }
	self.overall_analyzer = bench_analyzer(overall_info, overall_create_score_dict, json_data=overall_data)



    def view(self):
	view = View('primitives.html', 
		    {	"overall_score": int(self.overall_analyzer.json_data["overall_score"]),
			"cpu_score": int(self.cpu_analyzer.json_data["overall_score"]),
			"io_score": int(self.io_analyzer.json_data["overall_score"]),
			"network_score": int(self.network_analyzer.json_data["overall_score"]),
			"overall_breakdown": self.overall_analyzer.breakdown,
			"cpu_breakdown": self.cpu_analyzer.breakdown,
			"io_breakdown": self.io_analyzer.breakdown,
			"network_breakdown": self.network_analyzer.breakdown,
		    })
	return view

if __name__ == '__main__':
    Workload().run()

