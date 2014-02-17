import glob
import os
import salt
from minion import Minion
import pprint
from itertools import izip
import time
from salt.client.api import APIClient

MASTER_CONFIG_PATH = os.environ.get('SALT_MASTER_CONFIG', '/etc/salt/master')
MASTER_OPTIONS = salt.config.master_config(MASTER_CONFIG_PATH)

class SaltCommand(object):

    def __init__(self, command_kwargs, chain=None):
        self.kwargs = command_kwargs
        self.chain = chain

    def link(self, next_):

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

    def add(self, salt_cmd):
        """
        Adds a job to be tracked. The job is published with the salt
        apiclient. The resulting dict containing the job id and the minions
        associated with the job id are stored for later use.

        @param job_kwargs - The dictionary defining parameters of the job to
                            be published to salt.

        """

        #print "\n\n"
        #print "Wanting to publish a command"
        #print "Type of command: %s" % type(salt_cmd)
        #pprint.pprint(salt_cmd)

        pub = self.client.run(salt_cmd.kwargs)
        if pub:
            job = {'cmd': salt_cmd.kwargs,
                   'minions': pub['minions'],
                   'finished': set(),
                   'ret': {}}
            print "Published %s to %s with args %s" % (job['cmd']['fun'], job['cmd']['tgt'], job['cmd']['arg'])
            if salt_cmd.chain:
                job['chain'] = salt_cmd.chain
            self._jobs[pub['jid']] = job
            return True
        return False

    def is_job_finished(self, job):
        """
        Checks to see if a job has finished by compairing the set of affected
        minions to the set of finished minions.

        @param job - String job id

        """
        minions = set(job['minions'])
        finished = job['finished']
        if len(finished.intersection(minions)) >= len(minions):
            return True
        return False

    def wait(self, timeout):
        """
        Waits for all jobs so far to be finished.
        
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
                    print "Got results for pub %s to %s with args %s" % (job['cmd']['fun'], job['cmd']['tgt'], job['cmd']['arg'])
                    if job.get('chain'):
                        self.add(job['chain'])

            # Check to see if all jobs have finished
            if all([self.is_job_finished(job) for job in self._jobs.itervalues()]):                
                break

            # Check for timeout
            if time.time() > timeout_at:
                break

            # Delay a bit before checking again
            time.sleep(0.05)

        resp = {jid: job['ret'] for jid, job in self._jobs.iteritems()}
        return resp
                    
class SaltStateException(Exception):
    """
    Exception for when a call to state.sls is not completely successful.
    """

    def __init__(self, state, failures):
        """
        Initializes the exception.

        @param failures: List consisting of tuples and/or lists
                         Tuples should be of the form:
                         (minion id, state id, state, state function, comment)
                         A list should be for when the state can execute similar
                         to a templating error

        """
        msg = self.make_msg(state, failures)
        super(SaltStateException, self).__init__(msg)

    def make_msg(self, state, failures):
        msg = "State '%s' was unable to be applied due to the following reasons: \n%s\n"

        return msg % (state, "\n".join(self.failure_str(f) for f in failures))
        

    def failure_str(self, failure):
        if isinstance(failure, list):
            return "\n".join([i for i in failure])
        return "%s --- %s --- %s" % (failure[0], failure[4], failure[5])
        #return "Minion %s\nSls id: %s\nState: %s.%s\nName: %s\nComment: %s" \
        #    % failure


class Client(salt.client.LocalClient):
    """Provides an interface for dealing with the salt local client."""

    def __init__(self, event_store, credentials=None):
        """
        Initializes the client.
        @TODO - Allow salt options to be passed via argument

        @param credentials: Credential dict to pass to salt with every invocation

        """
        super(Client, self).__init__(mopts=MASTER_OPTIONS)
        self.event_store = event_store
        self.api_client = APIClient(opts=MASTER_OPTIONS)
        if credentials is None:
            credentials = {}
        self._credentials = credentials

    def minions_target(self, minions):
        """
        Convenience method for converting a Minion object or a list of
        Minion objects into a comma delimited string of minion ids for
        passing to salt

        """
        if isinstance(minions, Minion):
            minions = [minions]
        if isinstance(minions, list):
            minions = ','.join([minion.id_ for minion in minions])
        return minions

    def prepare_cmd_minions(self, target, expr_form, **kwargs):
        kwargs.update(self._credentials)
        kwargs.update({'mode': 'async',
                       'expr_form': expr_form,
                       'arg': (),
                       'fun': 'grains.items',
                       'tgt': target})
        return SaltCommand(kwargs)
        
    def prepare_cmd_sync_states(self, minions, **kwargs):
        target = self.minions_target(minions)
        kwargs.update(self._credentials)
        kwargs.update({'mode': 'async',
                       'tgt': target,
                       'fun': 'saltutil.sync_states',
                       'expr_form': 'list',
                       'arg': ()})
        return SaltCommand(kwargs)

    def prepare_cmd_set_grain(self, minions, key, value, **kwargs):
        target = self.minions_target(minions)
        kwargs.update(self._credentials)
        kwargs.update({'mode': 'async',
                       'tgt': target,
                       'fun': 'grains.setval',
                       'arg': (key, value),
                       'expr_form': 'list'})
        return SaltCommand(kwargs)

    def prepare_cmd_pillar_get(self, minions, key, default, ** kwargs):
        target = self.minions_target(minions)
        kwargs.update(self._credentials)
        kwargs.update({'mode': 'async',
                       'tgt': target,
                       'fun': 'pillar.get',
                       'arg': (key, default),
                       'expr_form': 'list'})
        return SaltCommand(kwargs)

    def prepare_cmd_network_ipaddrs(self, minions, interface, **kwargs):
        target = self.minions_target(minions)
        kwargs.update(self._credentials)
        kwargs.update({'mode': 'async',
                       'tgt': target,
                       'fun': 'network.ipaddrs',
                       'arg': (interface,),
                       'expr_form': 'list'})
        return SaltCommand(kwargs)
        
    def prepare_cmd_state(self, minions, state, sync=False, **kwargs):
        target = self.minions_target(minions)
        kwargs.update(self._credentials)
        kwargs.update({'mode': 'async',
                       'tgt': target,
                       'fun': 'state.sls',
                       'expr_form': 'list',
                       'arg': [state]})
        state_command = SaltCommand(kwargs)
        if sync:
            ret = self.prepare_cmd_sync_states(minions)
            ret.link(state_command)
        else:
            ret = state_command
        return ret

    def prepare_cmd(self, minions, func, **kwargs):
        target = self.minions_target(minions)
        kwargs.update(self._credentials)
        kwargs.update({'mode': 'async',
                       'tgt': target,
                       'fun': func,
                       'expr_form': 'list'})
        return SaltCommand(kwargs)

    def minions(self, target='*', expr_form='glob', **kwargs):
        """
        Creates a list of minions based on target and expr_form.

        @param target: Minion target
        @param expr_form: How to target minions
        @return List of minions

        """
        jobs = MultiJob(self.event_store)
        cmd = self.prepare_cmd_minions(target, expr_form)
        if (jobs.add(cmd)):
            timeout = cmd.kwargs.get('timeout') or 60
            resp = jobs.wait(timeout)
            # Only one job so take the first
            resp = resp.values()[0]

        # Create minion model for all returned grains
        return [Minion(grains) for id_, grains in resp.iteritems()]

    def run_multi(self, cmds, timeout=3600):
        jobs = MultiJob(self.event_store)
        for cmd in cmds:
            jobs.add(cmd)
        resp = jobs.wait(timeout)
        return resp

    def sync_states(self, target='*', expr_form='glob',  **kwargs):
        """
        Runs the salt method saltutil.sync_states on the targeted minions.

        @param target: Minion target
        @param expr_form: How to target minions
        @return: Dict describing which custom states were synced

        """
        kwargs.update(self._credentials)
        kwargs.update({'expr_form': expr_form,
                       'arg': (),})
       
        resp = self.cmd(target, 'saltutil.sync_states', **kwargs)
        return resp        

    def set_roles(self, minion_sets, role_sets, **kwargs):
        """
        Sets the roles value of the specified minions' grains and then updates
        the minion objects with the results
        
        @param minions: List of List of minions
        @param roles: List of list of roles.

        """
        jobs = MultiJob(self.event_store)
        timeout = kwargs.get('timeout', 60)
        for minions, roles in izip(minion_sets, role_sets):
            cmd = self.prepare_cmd_set_grain(minions, 'roles', roles)
            jobs.add(cmd)
                
        multi_resp = jobs.wait(timeout)

        # Get a unique set of minions
        all_minions = set()
        for minions in minion_sets:
            for minion in minions:
                all_minions.add(minion)
       
        # Update affected minions with role changes in grains 
        all_minions = {minion.id_: minion for minion in all_minions}
        for jid, job_resp in multi_resp.iteritems():
            for minion_id, value in job_resp.iteritems():
                all_minions[minion_id].update(value)

        all_minions = all_minions.values()
        for minion in all_minions:
            print "%s - %s" % (minion.id_, minion.roles)

    def cmd(self, minions, func, **kwargs):
        """
        Runs a single command. Wrapper for super.cmd.  Adds auth credentials.

        @param target - String salt target
        @param func - Salt function - 'pillar.get', 'network.ipaddrs', etc.
        
        @return - dict

        """        
        jobs = MultiJob(self.event_store)
        cmd = self.prepare_cmd(minions, func, **kwargs)
        jobs.add(cmd)
        resp = jobs.wait(kwargs.get('timeout') or 60)
        # Only ran one job so return it
        return resp.values()[0]

    def job(self, minions, func, **kwargs):
        """
        Wrapper for super.run_job.  Updates kwargs with credentials.
        
        @param target - Salt minion target
        @param func - Salt function - 'pillar.get', 'network.ipaddrs', etc.
        """
        jobs = MultiJob(self.event_store)
        cmd = self.prepare_cmd(minions, func, **kwargs)
        return jobs.add(cmd)

    def get_pillar(self, minions, what, default=None, **kwargs):
        """
        Returns pillar information for selected minions
        
        @param minions - List of minions
        @param what - String pillar information
        @param default - Default value to return
        @returns Dict

        """
        cmd = self.prepare_cmd_pillar_get(minions, what, default)
        jobs = MultiJob(self.event_store)
        jobs.add(cmd)
        resp = jobs.wait(kwargs.get('timeout') or 60)
        return resp.values()[0]

    def get_grains(self, minions, what, default=None, **kwargs):
        """
        Returns grain information
        @param minions - List of minions
        @param what - String grain information
        @param default - Default value to send back

        """
        return self.get_pillar_or_grains('grains.get',
                                         minions,
                                         what,
                                         default,
                                         **kwargs)

    def get_pillar_or_grains(self, method, minions, what, default, **kwargs):
        """
        Gets either pillar or grain information.

        @param method - String salt method 
                        Should be 'pillar.get' or 'grains.get'
        @return - dict

        """
        if isinstance(minions, Minion):
            minions = [minions]
        target = ','.join([m.id_ for m in minions])
        kwargs.update(self._credentials)
        kwargs.update({
            'arg': (what, default),
            'expr_form': 'list'
        })
        ret = self.cmd(target, method, **kwargs)
        return ret        

    def get_ips(self, minions, interface='public', default_interface='eth0', **kwargs):
        """
        Gets an ip address for a specific interface named in a pillar.
        Get 'public' or 'private' for example where public is mapped to eth0
        or private is mapped to eth2

        @param minions List of minions
        @param interface Name of the interface defined pillar interfaces
        @param default_interface Default interface to use if unable to
                                 locate one within pillar
        @return dictionary of ips for an interface keyed by minion id

        """       
        target = self.minions_target(minions)

        interface_dict = self.get_pillar(target, 'interfaces:%s' % interface, default_interface)

        # If there is only one interface, then we can get away with one salt call
        # for the ip address
        unique_interfaces = set([i for minion_id, i in interface_dict.iteritems()])
        if len(unique_interfaces) == 1:
            jobs = MultiJob(self.event_store)            
            cmd = self.prepare_cmd_network_ipaddrs(target, unique_interfaces.pop())
            jobs.add(cmd)
            ret = jobs.wait(kwargs.get('timeout') or 60)
            # multijobs wait returns dictionary keyed by job id. Take the first(and only) job return
            ret = ret.values()[0]
            
        # Otherwise we have to iterate
        else :
            ret = {}
            jobs = MultiJob(self.event_store)
            for minion_id, interface in interface_dict:
                cmd = self.prepare_cmd_network_ipaddrs(minion_id, interface)
                jobs.add(cmd)
            resp = jobs.wait(kwargs.get('timeout') or 60)
            for jid, job_ret in jobs:
                ret.update(job_ret)
        return ret
