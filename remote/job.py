import os
import salt
import time
from salt.client.api import APIClient

MASTER_CONFIG_PATH = os.environ.get('SALT_MASTER_CONFIG', '/etc/salt/master')
MASTER_OPTIONS = salt.config.master_config(MASTER_CONFIG_PATH)


class SaltJob(object):
    """
    Hold information pertaining to a salt job
    """

    def __init__(self, command_kwargs, chain=None):
        """
        Salt job constructor

        @param command_kwargs - Kwarg dictionary to send to an APIClient
        @param chain - Optional salt job to link this job to in sequence

        """
        self.kwargs = command_kwargs
        self.chain = chain

    def link(self, next_):
        """
        Links next_ to the end of the sequence of salt jobs this job is in.

        @param next_ - SaltJob to append to end of sequence.

        """
        current = self
        while current.chain is not None:
            current = current.chain
        current.chain = next_


class MultiJob(object):

    def __init__(self, event_store):
        """
        MultiJob constructor

        @param event_store - Managed dict proxy object that a job poller
                             stores events into
        """
        self._jobs = {}
        self.event_store = event_store
        self.client = APIClient(opts=MASTER_OPTIONS)

    def add(self, salt_job):
        """
        Adds a job to be tracked. The job is published with the salt
        apiclient. The resulting dict containing the job id and the minions
        associated with the job id are stored for later use.

        @param salt_job - SaltCommand object containing a dictionary defining
            parameters of the salt job to be published
        @return - Boolean True for successful publish, Boolean False otherwise

        """
        pub = self.client.run(salt_job.kwargs)
        if pub:
            job = {'cmd': salt_job.kwargs,
                   'minions': pub['minions'],
                   'finished': set(),
                   'ret': {}}

            # Check to see if this command is part of a sequence of commands.
            if salt_job.chain:
                job['chain'] = salt_job.chain
            self._jobs[pub['jid']] = job
            return True
        return False

    def is_job_finished(self, job):
        """
        Checks to see if a job has finished by compairing the set of affected
        minions to the set of finished minions.

        @param job - Dictionary of tracked job info
        @return - Boolean true for finished, Boolean false otherwise

        """
        minions = set(job['minions'])
        finished = job['finished']
        if len(finished.intersection(minions)) >= len(minions):
            return True
        return False

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
            for jid, job in self._jobs.items():

                # Stop looking if the job is finished
                if self.is_job_finished(job):
                    continue

                # Check the event store
                raw = self.event_store.get_event(jid)
                if raw is not None and 'return' in raw:
                    job['finished'].add(raw['id'])
                    job['ret'][raw['id']] = raw['return']

                if self.is_job_finished(job):
                    if job.get('chain'):
                        self.add(job['chain'])

            # Check to see if all jobs have finished
            if all([self.is_job_finished(job)
                    for job in self._jobs.itervalues()]):
                break

            # Check for timeout
            if time.time() > timeout_at:
                break

            # Delay a bit before checking again
            time.sleep(0.05)

        resp = {jid: job['ret'] for jid, job in self._jobs.iteritems()}
        return resp
