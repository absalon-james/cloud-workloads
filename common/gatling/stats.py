
class Action(list):
    """
    Base class for modeling an action in the gatling simulation.log.
    An action should be a string split by '\t'
    """

    @property
    def action(self):
        """
        Returns the type of action(run, request, scenario

        :returns: String type of action
        """
        return self[0]

class RunAction(Action):
    """
    Models the run action in a gatling simulation.log file
    <action> <start time> <simulation name> <simulation description>
    """

    @property
    def start(self):
        """
        Returns the start timestamp.

        :returns: Integer timestamp
        """
        return int(self[1])

    @property
    def name(self):
        """
        Returns the name

        :returns: String name of the run action
        """
        return self[2]

    @property
    def description(self):
        """
        Returns the description

        :returns: String description of the run action
        """
        return self[3]

class RequestAction(Action):
    """
    Models a request action in the simulation.log file
    <action> <scenario name> <user id> <groups> <request name> <request start date> <request end date> <response start date> <response end date> <status> <extra info>
    """

    @property
    def scenario_name(self):
        """
        Returns name of the scenario

        :returns: String name of the scenario
        """
        return self[1]

    @property
    def user_id(self):
        """
        Returns the user id

        :returns: Integer user id
        """
        return int(self[2])

    @property
    def request_name(self):
        """
        Returns the name of the request

        :returns: Name of the request
        """
        return self[4]

    @property
    def request_start(self):
        """
        Returns the start request start time

        :returns: Integer request start time
        """
        return int(self[5])

    @property
    def request_end(self):
        """
        Returns the end request end time

        :returns: Integer request end time
        """
        return int(self[6])

    @property
    def response_start(self):
        """
        Returns the response start time

        :returns: Integer response start time
        """
        return int(self[7])

    @property
    def response_end(self):
        """
        Returns the end response time

        :returns: Integer response end time
        """
        return int(self[8])

    @property
    def response_time(self):
        """
        Returns the difference in ms between request start and response start

        :returns: Integer difference in ms
        """
        return self.response_start - self.request_start

    @property
    def status(self):
        """
        Returns the request status

        :returns: String request status
        """
        return self[9]

    @property
    def success(self):
        """
        Returns whether or not the request was successful

        :returns: Boolean indication
        """
        return self[9] == 'OK'

    @property
    def info(self):
        """
        Returns any extra info

        :returns: String info
        """
        return self[10]

class ScenarioAction(Action):
    """
    Models a scenario action from a gatling simulation.log file
    <action> <scenario name> <user-id> <start time> <end time>
    """

    @property
    def name(self):
        """
        Returns the name of the scenario

        :returns: string
        """
        return self[1]

    @property
    def user_id(self):
        """
        Returns the user id

        :returns: Integer user id
        """
        return int(self[2])

    @property
    def start_time(self):
        """
        Returns the start time

        :returns: Integer start time
        """
        return int(self[3])

    @property
    def end_time(self):
        """
        Returns the end time

        :returns: Integer end time
        """
        return int(self[4])

class Stats(dict):
    """
    Models and groups all of the actions inside of a simulation.log file
    """

    _action_classes = {
        'RUN': RunAction,
        'REQUEST': RequestAction,
         'SCENARIO': ScenarioAction}

    @property
    def scenarios(self):
        return self._actions['SCENARIO']

    @property
    def requests(self):
        return self._actions['REQUEST']

    @property
    def runs(self):
        return self._actions['RUN']

    @property
    def duration(self):
        return self.end_time - self.start_time

    @property
    def times(self):
        return xrange(self.start_time, self.end_time, 1000)

    @property
    def requests_per_second_plot(self):
        points = []
        total = 0
        for time in self.times:
            new_total = len([True for it in self.requests if time > it.response_end])
            points.append({'x': time, 'y': new_total - total})
            total = new_total
        return points

    @property
    def sessions_per_second_plot(self):
        points = []
        for time in self.times:
            sessions = len([True for it in self.scenarios if time >= it.start_time and time <= it.end_time])
            points.append({'x': time, 'y': sessions})
        return points

    @property
    def response_times_plot(self):
        response_times = {
            't <= 800ms': 0,
            '800ms < t <= 1200ms': 0,
            't > 1200ms': 0,
            'failed': 0
        }
        
        for r in self.requests:
            if r.success == False:
                response_times['failed'] += 1
                continue
            if r.response_time <= 800:
                response_times['t <= 800ms'] += 1
            elif r.response_time <= 1200:
                response_times['800ms < t <= 1200ms'] += 1
            else:
                response_times['t > 1200ms'] += 1
        return response_times

    def __init__(self, iteration):

        self._actions = {
            'RUN': [],
            'REQUEST': [],
            'SCENARIO': []
        }

        with open(iteration.simulation_log) as logfile:
            for line in logfile:
                line = line.strip("\n").split("\t")
                self._actions[line[0]].append(self._action_classes[line[0]](line))

        self.end_time = max([it.end_time for it in self.scenarios])
        self.start_time = min([it.start_time for it in self.scenarios])
