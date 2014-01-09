import json


class bench_analyzer(object):

    def __init__(self, score_info, create_score_dict,
                 data_file_name=None, json_data=None):
        '''
        data_file_name:    string:   name of file containing json data for
                                     bench output
        score_info:        dict:     key is test name, val is dict of the form
                                     {"normalizers": val, "weight": val}
            normalizers:             normalizers to turn score into percentage
                                     of "top performance capable" ex. 10000.0
            weights:                 weights for each score to get weighted 
                                     avg ex. 2.0
        create_score_dict: function: meant to take raw json data from bench
                                     and turn it into a dict containing only
                                     names of tests to be included and their
                                     scores
        '''
        self.score_info = score_info

        #raw json data that came from the json file
        if data_file_name is not None:
            self.json_data = self._get_json_from_file(data_file_name)
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

    def _get_json_from_file(self, data_file_name):
        '''
        Reads the file into a JSON object.
        If file doesn't exist or is empty [] is returned
        If bad JSON given error is thrown
        '''
        data_json = []
        with open(data_file_name, 'r') as data_file:
            data_json = json.load(data_file)
        return data_json

    def get_breakdown_table(self, normal_scores):
        breakdown_rows = ["<tr> \n\
                    <td class=\"breakdown\">%s</td> \n\
                    <td class=\"breakdown\">%s</td> \n\
                    <td class=\"breakdown\">%s</td> \n\
                    </tr>\n" % (test_name, val["weight"],
                                int(normal_scores[test_name]))
                                for test_name, val in self.score_info.iteritems()]

        return "<table> \n\
                    <tr> \n\
                    <td class=\"breakdown\">Input Label</td> \n\
                    <td class=\"breakdown\">Weight</td> \n\
                    <td class=\"breakdown\">Percentage</td> \n\
                    </tr> \n\
                    %s \n\
                    </table>" % "".join(breakdown_rows)
    

    def analyze(self):
        def _normalize_score(test_name, score):
            normalizer = float(self.score_info[test_name]["normalizer"])
            return 100 * float(score) / normalizer

        def _weigh_scores(test_name, score):
            weight = float(self.score_info[test_name]["weight"])
            return weight * float(score)

        def _avg(num_list, weight_total):
            return sum(num_list)/float(weight_total)

        normal_scores_dict = {test_name: _normalize_score(test_name, score)
                              for test_name, score 
                              in self.score_dict.iteritems()}

        weighted_normal_score_list = [_weigh_scores(test_name, score)
                                      for test_name, score 
                                      in normal_scores_dict.iteritems()]

        weight_total = sum([val["weight"]
                            for val 
                            in self.score_info.values()])

        self.overall_score = _avg(weighted_normal_score_list, weight_total)
        self.breakdown = self.get_breakdown_table(normal_scores_dict)

        self.json_data["overall_score"] = self.overall_score
        self.json_data["status"] = "Success"



