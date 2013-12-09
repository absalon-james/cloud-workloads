import json


class bench_analyzer(object):
    def __init__(self, score_info, create_score_dict,
                 file_name=None, json_data=None):
        '''
        file_name:         string:   name of file containing json data for
                                     bench output
        score_info:        dict:     key is test name, val is dict of the form
                                     {"normalizers": val, "weight": val}
            normalizers: normalizers to turn score into percentage of "top
                                     performance capable" ex. 10000.0
            weights:     weights for each score to get weighted avg ex. 2.0
        create_score_dict: function: meant to take raw json data from bench
                                     and turn it into a dict containing only
                                     names of tests to be included and their
                                     scores
        '''
        self.file_name = file_name
        self.score_info = score_info

        #raw json data that came from the json file
        if file_name is not None:
            self.json_data = self._get_json_from_file(file_name)
        else:
            self.json_data = json_data

        if self.json_data is None:
            raise Exception("No benchmark data available.")

        #dictionary of all the available scores from the json
        #ex. {"test_name": 4000.0}
        self.score_dict = create_score_dict(self.json_data)
        #create string with html for the table and rows of the breakdown
        breakdown_table_rows = ["<tr> \n\
                    <td class=\"breakdown\">%s</td> \n\
                    <td class=\"breakdown\">%s</td> \n\
                    <td class=\"breakdown\">%s</td> \n\
                    </tr>\n" % (key, val["weight"], val["normalizer"])
                                for key, val in score_info.iteritems()]
        breakdown_table = "<table> \n\
                    <tr> \n\
                    <td class=\"breakdown\">Input Label</td> \n\
                    <td class=\"breakdown\">Weight</td> \n\
                    <td class=\"breakdown\">Highest Score</td> \n\
                    </tr> \n\
                    %s \n\
                    </table>" % "".join(breakdown_table_rows)
        self.breakdown = breakdown_table
        self.analyze()

    def _get_json_from_file(self, file_name):
        '''
        Reads the file into a JSON object.
        If file doesn't exist or is empty [] is returned
        If bad JSON given error is thrown
        '''
        data_json = []
        with open(file_name, 'r') as data_file:
            data_json = json.load(data_file)
        return data_json

    def _avg(self, num_list, weight_total):
        return sum(num_list)/float(weight_total)

    def analyze(self):
        normal_scores_dict = {key: (100 * float(val) /
                                    float(self.score_info[key]["normalizer"]))
                              for key, val in self.score_dict.iteritems()}
        weighted_normal_scores_list = [self.score_info[key]["weight"]*val
                                       for key, val in
                                       normal_scores_dict.iteritems()]
        weight_total = sum([val["weight"]
                            for val in self.score_info.values()])
        self.json_data["overall_score"] = self._avg(
            weighted_normal_scores_list, weight_total)
        self.json_data["status"] = "Success"
