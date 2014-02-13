from operator import attrgetter

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
    <action> <scenario name> <user id> <groups> <request name>
        <request start date> <request end date> <response start date>
        <response end date> <status> <extra info>
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
        'SCENARIO': ScenarioAction
    }

    @property
    def scenarios(self):
        """
        Returns all scenerios

        :return: List
        """
        return self._actions['SCENARIO']

    @property
    def requests(self):
        """
        Returns all requests

        :return: List
        """
        return self._actions['REQUEST']

    @property
    def runs(self):
        """
        Returns all runs

        :return: List
        """
        return self._actions['RUN']

    @property
    def duration(self):
        """
        Returns the total time.

        :return: Integer
        """
        return self.end_time - self.start_time

    @property
    def times(self):
        """
        Returns an xrange starting with the start time and
        1000 ms intervals all the way up to the end time.

        :return: xrange
        """
        return xrange(self.start_time, self.end_time, 1000)

    @property
    def requests_per_second_plot(self):
        """
        Counts the number of requests that have completed from
        second to second and records them into a plot for graphing.

        :return: List of datapoints
        """
        points = []
        total = 0
        for time in self.times:
            def finished(total, request):
                if time > request.response_end:
                    total += 1
                return total
            new_total = reduce(finished, self.requests, 0)
            points.append({'x': time, 'y': new_total - total})
            total = new_total
        return points

    @property
    def sessions_per_second_plot(self):
        """
        Counts the number of active sessions at each 1000 ms interval and
        records them into a plot for graphing.

        :return: List of datapoints
        """
        points = []
        for time in self.times:
            def active(total, session):
                if time >= session.start_time and time <= session.end_time:
                    total += 1
                return total
            sessions = reduce(active, self.scenarios, 0)
            points.append({'x': time, 'y': reduce(active, self.scenarios, 0)})
        return points

    @property
    def response_times_plot(self):
        """
        Creates a distribution of response times grouping them into
        4 main groups.

        :return: Dictionary
        """
        response_times = {
            't <= 800ms': 0,
            '800ms < t <= 1200ms': 0,
            't > 1200ms': 0,
            'failed': 0
        }

        for r in self.requests:
            if r.success is False:
                response_times['failed'] += 1
                continue
            if r.response_time <= 800:
                response_times['t <= 800ms'] += 1
            elif r.response_time <= 1200:
                response_times['800ms < t <= 1200ms'] += 1
            else:
                response_times['t > 1200ms'] += 1
        return response_times

    def update(self, simulation_log_io):

        for line in simulation_log_io:
            line = line.strip("\n").split("\t")
            if line[0] in self._actions:
                self._actions[line[0]].append(
                  self._action_classes[line[0]](line))

        self.end_time = max(self.scenarios, key=attrgetter("end_time")).end_time
        self.start_time = min(self.scenarios, key=attrgetter("start_time")).end_time
        

    def __init__(self):
        """
        Inits the stats object parsing through the simulation.log file
        indicated by the iteration.

        :param iteration: Gatling iteration to provide stats for.
        """
        self._actions = {
            'RUN': [],
            'REQUEST': [],
            'SCENARIO': []
        }
