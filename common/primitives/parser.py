import json


class bench_parser(dict):
    def __init__(self, lines):
        super(bench_parser, self).__init__(self.parse(lines))

    def update_with_json(self, str_data):
            json_data = json.loads(str_data)
            self.update(json_data)


class cpu_parser(bench_parser):
    unixbench_json_file_tag = "JSON_FILE:"

    @classmethod
    def parse(self, lines):
        for line in lines:
            if line.startswith(self.unixbench_json_file_tag):
                json_data_file = line.split()[1]
                return {'json_data_file': json_data_file}
        return None


class io_parser(bench_parser):
    filebench_summary_tag = "IO Summary:"

    def __init__(self):
        super(bench_parser, self).__init__()

    def parse(self, cmd, lines):
        for line in lines:
            if self.filebench_summary_tag in line:
                mbps = line.split(", ")[-3].replace("mb/s", "")
                test_name = cmd.split()[-1].split('/')[-1]
                self[test_name] = float(mbps)


class network_parser(bench_parser):

    def parse(self, lines):
        iperf_data = {"window_sizes": [], "connections": {}}
        for line in lines:
            words = line.split()
            if (words[0] == "TCP"):
                iperf_data["window_sizes"].append(words[3])
            elif(words[0] == "[" and words[1] != "ID]"):
                conn_num = words[1].replace("]", "")
                if (words[2] == "local"):
                    iperf_data["connections"][conn_num] = {
                        "local_ip": words[3],
                        "local_port": words[5],
                        "remote_ip": words[8],
                        "remote_port": words[10]
                    }
                else:
                    interval_list = words[2].split("-")
                    iperf_data["connections"][conn_num] = {
                        "interval_start": interval_list[0],
                        "interval_stop": interval_list[1],
                        "transfer_mb": words[4],
                        "bandwidth_mb/sec": words[6]
                    }

        return iperf_data
