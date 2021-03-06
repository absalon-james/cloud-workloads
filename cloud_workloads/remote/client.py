from minion import Minion
from itertools import izip
from job import MultiJob, SaltJob


class Client(object):
    """Provides an interface for dealing with the salt local client."""

    def __init__(self):
        """
        Initializes the client.

        """
        pass

    def minions_target(self, minions):
        """
        Convenience method for converting a Minion object or a list of
        Minion objects into a comma delimited string of minion ids for
        passing to salt

        @param minions - Single Minion, List of Minions or string
        @return - Aims to return comma delimited list of minion ids

        """
        if isinstance(minions, Minion):
            minions = [minions]
        if isinstance(minions, list):
            minions = ','.join([minion.id_ for minion in minions])
        return minions

    def prepare_job_minions(self, target, expr_form, **kwargs):
        """
        Prepares a salt command to get grains.items for all minions
        matching the target.

        @param target - String target
        @param expr_form - String expression form ('glob','list', etc')
        @return SaltJob

        """
        kwargs.update({'expr_form': expr_form,
                       'arg': (),
                       'fun': 'grains.items',
                       'tgt': target})
        return SaltJob(kwargs)

    def prepare_job_sync_states(self, minions, **kwargs):
        """
        Prepares a salt command to synchronize states. Necessary for any
        custom state modules.

        @param minions - List of minions, Single minion, or string
        @return - SaltJob

        """
        target = self.minions_target(minions)
        kwargs.update({'tgt': target,
                       'fun': 'saltutil.sync_states',
                       'expr_form': 'list',
                       'arg': ()})
        return SaltJob(kwargs)

    def prepare_job_set_grain(self, minions, key, value, **kwargs):
        """
        Prepares a salt command to set the value of grain.

        @param minions - List of minions, single minion, or string
        @param key - String key indicating which grain to set
        @param value - Value to set the grain to.
        @return - SaltJob

        """
        target = self.minions_target(minions)
        kwargs.update({'tgt': target,
                       'fun': 'grains.setval',
                       'arg': (key, value),
                       'expr_form': 'list'})
        return SaltJob(kwargs)

    def prepare_job_pillar_get(self, minions, key, default, **kwargs):
        """
        Prepares a salt command to get a value out of pillar.

        @param minions - Single minion, list of minions, or string
        @param key - String key indicating which information to get out of
            pillar
        @param default - Default value to return if key is not present in
            pillar
        @return - SaltJob

        """
        target = self.minions_target(minions)
        kwargs.update({'tgt': target,
                       'fun': 'pillar.get',
                       'arg': (key, default),
                       'expr_form': 'list'})
        return SaltJob(kwargs)

    def prepare_job_network_ipaddrs(self, minions, interface, **kwargs):
        """
        Prepares a salt command to get the ip address for a particular
        interface.

        @param minions - Single minion, list of minions, or a string
        @param interface - String interface to get ip addresses for
            ('eth0','eth1', etc)
        @return SaltJob

        """
        target = self.minions_target(minions)
        kwargs.update({'tgt': target,
                       'fun': 'network.ipaddrs',
                       'arg': (interface,),
                       'expr_form': 'list'})
        return SaltJob(kwargs)

    def prepare_job_state(self, minions, state, sync=False, **kwargs):
        """
        Prepares a salt command to apply a sls state file to minions.
        Optionally calls saltutil.sync_states prior to state.sls(useful for
        handling custom state modules).

        @param minions - single minion, list of minions, or a string
        @param state - String indicating which sls file to apply
        @param sync - Do a saltutil.sync_states first?
        @return SaltJob

        """
        target = self.minions_target(minions)
        kwargs.update({'tgt': target,
                       'fun': 'state.sls',
                       'expr_form': 'list',
                       'arg': [state]})
        state_job = SaltJob(kwargs, retcodes=set([0, 2]))

        # Optionally sync for custom states
        if sync:
            ret = self.prepare_job_sync_states(minions)
            ret.link(state_job)
        else:
            ret = state_job
        return ret

    def prepare_job(self, minions, func, retcodes=None, **kwargs):
        """
        Prepares a salt command that runs the requested salt function.
        All other commands can probably wrap this command.

        NOTE - arg and kwarg sent to salt should already be in kwargs.

        @param minions - single minion, list of minions, or string
'       @param func - String indicating salt method to run
        @param retcodes - Set of acceptable integer return codes
        @return SaltJob

        """
        target = self.minions_target(minions)
        kwargs.update({'tgt': target,
                       'fun': func,
                       'expr_form': 'list'})
        return SaltJob(kwargs, retcodes=retcodes)

    def minions(self, target='*', expr_form='glob', **kwargs):
        """
        Creates a list of minions based on target and expr_form.

        @param target: Minion target
        @param expr_form: How to target minions
        @return List of minions

        """
        job = self.prepare_job_minions(target, expr_form)
        resp = self.run_jobs([job], job.kwargs.get('timeout') or 60)
        # Only one job so take the first
        resp = resp.values()[0]

        # Create minion model for all returned grains
        return [Minion(grains) for id_, grains in resp.iteritems()]

    def run_jobs(self, jobs, timeout=3600):
        """
        Runs multiple jobs or a single job.

        @param jobs - Single SaltJob or a list of SaltJobs
        @param timeout - Integer number of seconds to wait for all jobs
            to complete

        """
        # Convert to list if given single job
        if isinstance(jobs, SaltJob):
            jobs = [jobs]

        multi = MultiJob()
        for job in jobs:
            multi.add(job)
        resp = multi.wait(timeout)
        return resp

    def set_roles(self, minion_sets, role_sets, **kwargs):
        """
        Sets the roles value of the specified minions' grains and then updates
        the minion objects with the results

        @param minions: List of List of minions
        @param roles: List of list of roles.

        """
        timeout = kwargs.get('timeout', 60)
        jobs = []
        for minions, roles in izip(minion_sets, role_sets):
            jobs.append(self.prepare_job_set_grain(minions, 'roles', roles))
        multi_resp = self.run_jobs(jobs, timeout)

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

    def cmd(self, minions, func, **kwargs):
        """
        Runs a single command. Wrapper for super.cmd.

        @param target - String salt target
        @param func - Salt function - 'pillar.get', 'network.ipaddrs', etc.
        @return - dict

        """
        timeout = kwargs.get('timeout') or 3600
        jobs = [self.prepare_job(minions, func, **kwargs)]
        resp = self.run_jobs(jobs, timeout)
        return resp.values()[0]

    def job(self, minions, func, **kwargs):
        """
        Fires off a job asynchronously and doesn't care/know about the
        result.

        @param func - Salt function - 'pillar.get', 'network.ipaddrs', etc.
        """
        multi = MultiJob()
        job = self.prepare_job(minions, func, **kwargs)
        return multi.add(job)

    def get_pillar(self, minions, what, default=None, **kwargs):
        """
        Returns pillar information for selected minions

        @param minions - List of minions
        @param what - String pillar information
        @param default - Default value to return
        @returns Dict

        """
        jobs = [self.prepare_job_pillar_get(minions, what, default)]
        resp = self.run_jobs(jobs, kwargs.get('timeout') or 60)
        return resp.values()[0]

    def get_ips(self,
                minions,
                interface='public',
                default_interface='eth0',
                **kwargs):
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

        interface_dict = self.get_pillar(target,
                                         'interfaces:%s' % interface,
                                         default_interface)

        # If there is only one interface, then we can get away with one salt
        # call for the ip address
        unique_interfaces = \
            set([i for minion_id, i in interface_dict.iteritems()])
        if len(unique_interfaces) == 1:
            jobs = [self.prepare_job_network_ipaddrs(target,
                                                     unique_interfaces.pop())]
            ret = self.run_jobs(jobs, kwargs.get('timeout') or 60)
            ret = ret.values()[0]

        # Otherwise we have to iterate
        else:
            ret = {}
            jobs = []
            for minion_id, interface in interface_dict:
                jobs.append(
                    self.prepare_job_network_ipaddrs(minion_id, interface))
            resp = self.run_jobs(jobs, kwargs.get('timeout') or 60)
            for jid, job_ret in resp:
                ret.update(job_ret)
        return ret
