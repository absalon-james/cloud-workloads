import os
import salt
import time
from salt.client.api import APIClient
from handler import Handler, UnfinishedException, UnsuccessfulException, \
    RetcodeException, FailedStateSlsException

MASTER_CONFIG_PATH = os.environ.get('SALT_MASTER_CONFIG', '/etc/salt/master')
MASTER_OPTIONS = salt.config.master_config(MASTER_CONFIG_PATH)


class MultiJobException(Exception):
    """
    Combines multiple exceptions into one and tries to produce human readable
    output from multiple exceptions

    """

    def __init__(self, exceptions):
        """
        Constructor

        @param exceptions - Collection of exceptions to combine together
        """
        msg = self.make_msg(exceptions)
        super(MultiJobException, self).__init__(msg)

    def make_msg(self, exceptions):
        """
        Produces a string containing a brief summary followed by a newline
        delimited list of exception messages. One per xception.

        @param exceptions - Collection of exceptions
        @return String

        """
        exceptions = [str(e) for e in exceptions]
        return ("The following errors were encountered when running multiple"
                " salt jobs:\n%s") % "\n".join([str(e) for e in exceptions])


class SaltJob(object):
    """
    Holds information pertaining to a salt job
    """

    # Maps salt functions to validate functions in this class
    validate_funcs = {
        'state.sls': 'validate_state_sls'
    }

    def __init__(self, command_kwargs, retcodes=None, chain=None):
        """
        Salt job constructor

        @param command_kwargs - Kwarg dictionary to send to an APIClient
        @param retcodes - Set of acceptable process return codes. If none
            provided, only retcode 0 will be acceptable
        @param chain - Optional salt job to link this job to in sequence

        """
        # Kwargs passed to the salt api client
        self.kwargs = command_kwargs
        # Acceptable return codes
        self.goodcodes = retcodes or set([0])
        # Next in a sequence of SaltJob's
        self.chain = chain
        # Job id created by publish
        self.jid = None
        # Minions identified by publish
        self.minions = None
        # Minions that have finished so far
        self.finished_minions = set()
        # Response
        self.ret = {}
        # Events collected from salt
        self.events = {}
        # Handler - raises exceptions and output
        self.handler = Handler()

    def link(self, next_):
        """
        Links next_ to the end of the sequence of salt jobs this job is in.

        @param next_ - SaltJob to append to end of sequence.

        """
        current = self
        while current.chain is not None:
            current = current.chain
        current.chain = next_

    def is_finished(self):
        """
        Computes the difference between the set of expected minions and the
        set of minions that have returned so far.  The job is finished when
        there are no minions in the difference set.

        @param return Boolean True for yes, Boolean false otherwise

        """
        return self.minions.issubset(self.finished_minions)

    def set_pub_data(self, pub_data):
        """
        Handles the publish data returned from a call to run on an APIClient
        object

        @param pub_data - Dictionary containing affected minion ids and a jid
            or an empty dict representing a publish failure
        """
        # Check for bad publish, emit any output
        self.handler.handle_publish(self, pub_data)

        # Set jid and minions
        self.jid = pub_data['jid']
        self.minions = set(pub_data['minions'])

    def add_minion_return(self, raw):
        """
        Adds a minion return or an event to the tracked data.
        The return/event must have the fields 'id' and 'return' to be
        considered part of the job's response

        @param raw - Dictionary representing event or minion return

        """
        if raw is not None:
            # Save the event
            self.events[raw['id']] = raw
            if 'return' in raw:
                self.finished_minions.add(raw['id'])
                self.ret[raw['id']] = raw['return']

    def validate_func(self):
        """
        Returns a validate function or none based upon the salt function
        used.  Example: state.sls in salt has some special output that needs
        to be validated a little differently.

        @return - A validating function or None

        """
        salt_method = self.kwargs['fun']
        validate_name = self.validate_funcs.get(salt_method)
        if validate_name is not None:
            return getattr(self, validate_name, None)
        return None

    def validate(self):
        """
        Validates the job. Exceptions are raised by the handler.
        Checks that the job finished
        Checks that all events were success
        Checks that all retcodes were acceptable
        Calls any custom validation methods that are necessary.

        """
        # Check that all minions have returned
        if not self.is_finished():
            self.handler.handle_unfinished(self)

        # Checked that all events for the minion are success
        if not all([e['success'] for e in self.events.itervalues()]):
            self.handler.handle_unsuccessful(self)

        # Check all retcodes
        allcodes = set()
        for e in self.events.itervalues():
            allcodes.add(e.get('retcode', 1))
        if len(allcodes.difference(self.goodcodes)) > 0:
            self.handler.handle_retcodes(self)

        # Do any custom validation base on the salt function
        func = self.validate_func()
        if func:
            func()

    def validate_state_sls(self):
        """
        Validates this job against for the salt function 'state.sls'.

        """
        for e in self.events.itervalues():
            if not all([ret['result'] for ret in e['return'].itervalues()]):
                self.handler.handle_failed_state_sls(self)
                break


class MultiJob(object):

    def __init__(self):
        """
        MultiJob constructor

        """
        self._jobs = {}
        self.client = APIClient(opts=MASTER_OPTIONS)
        self.handler = Handler()

    def add(self, job):
        """
        Adds a job to be tracked. The job is published with the salt
        apiclient. The resulting dict containing the job id and the minions
        associated with the job id are stored for later use.

        @param salt_job - SaltCommand object containing a dictionary defining
            parameters of the salt job to be published
        @return - Boolean True for successful publish, Boolean False otherwise

        """
        pub_data = self.client.run(job.kwargs)
        job.set_pub_data(pub_data)
        self._jobs[job.jid] = job

    def is_finished(self):
        """
        Checks to see if all jobs are finished.

        @return - Boolean true for finished, Boolean false otherwise

        """
        return all([job.is_finished() for job in self._jobs.itervalues()])

    def should_process_event(self, event):
        """
        Checks whether or not we need to process an event.
        Events should have a jid and a return.
        The jid should be a job belonging to this MultiJob
        The job should not be finished yet.

        @param event - Dictionary representing an event.
        @return Boolean True for yes, False otherwise.

        """
        jid = event.get('jid')
        ret = event.get('return')
        if jid is None or ret is None:
            return False

        if jid not in self._jobs:
            return False

        job = self._jobs[jid]
        if job.is_finished():
            return False
        return True

    def wait(self, timeout):
        """
        Waits for all jobs so far to be finished. If a job finishes that is
        part of a sequence of jobs, the next job in the sequenced is
        published.

        @param timeout - Float or int describing number of seconds to wait
            in total before returning.
        @return dict - Dictionary of responses

        """
        start = time.time()
        timeout_at = start + timeout
        while True:

            # Break on timeout
            if time.time() > timeout_at:
                break

            # Listen for all events with tag set to ''.
            # Need to be able to listen for multiple jobs.
            event = self.client.get_event(tag='', wait=0.25)

            # Check for no event received
            if event is None:
                continue

            if self.should_process_event(event):
                job = self._jobs[event.get('jid')]
                job.add_minion_return(event)
                if job.is_finished():
                    self.handler.handle_finish(job)
                    if job.chain:
                        self.add(job.chain)

            # Break on all jobs finished
            if self.is_finished():
                break

        errors = []
        # Validate our jobs
        for jid, job in self._jobs.iteritems():
            try:
                job.validate()
            except (UnfinishedException,
                    UnsuccessfulException,
                    RetcodeException,
                    FailedStateSlsException) as e:
                errors.append(e)
        if errors:
            raise MultiJobException(errors)

        resp = {jid: job.ret for jid, job in self._jobs.iteritems()}
        return resp
