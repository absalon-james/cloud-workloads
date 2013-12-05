import parser
import json

class parser(object):
    def _get_json_from_file(self, file_name):
	'''
        Reads the file into a JSON object.
        If file doesn't exist or is empty [] is returned
        If bad JSON given error is thrown
        '''
        data_json = []
        with open(file_name, 'r') as data_file:
	    try:
                data_json = json.load(data_file)
	    except ValueError, e:
		pass
        return data_json

class cpu_parser(parser):
    unixbench_json_file_tag = "JSON_FILE:"

    def parse(self, lines):
	for line in lines
	    if line.startswith(self.unixbench_json_file_tag):
	        json_data_file = line.split()[1]
		return self._get_json_from_file(json_data_file)
	return None

class io_parser(parser):

    def parse(self, lines):
	for line in lines:
            if self.filebench_summary_tag in line:
                mbps = line.split(", ")[-3].replace("mb/s", "")
                test_name = cmd[-1].split("/")[-1]
                fb_data[test_name] = float(mbps)


class network_parser(parser):

    def parser(self, lines):
	iperf_data = {"window_sizes": [], "connections": {}}
        for line in lines:
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



