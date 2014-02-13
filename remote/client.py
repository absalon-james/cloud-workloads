import os
import salt
from minion import Minion
import pprint

MASTER_CONFIG_PATH = os.environ.get('SALT_MASTER_CONFIG', '/etc/salt/master')
MASTER_OPTIONS = salt.config.master_config(MASTER_CONFIG_PATH)

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


class Client(object):
    """Provides an interface for dealing with the salt local client."""

    def __init__(self, credentials=None):
        """
        Initializes the client.
        @TODO - Allow salt options to be passed via argument

        @param credentials: Credential dict to pass to salt with every invocation

        """
        self._client = salt.client.LocalClient(mopts=MASTER_OPTIONS)
        if credentials is None:
            credentials = {}
        self._credentials = credentials

    def minions(self, target='*', expr_form='glob'):
        """
        Creates a list of minions based on target and expr_form.

        @param target: Minion target
        @param expr_form: How to target minions
        @return List of minions

        """
        kwargs = {'expr_form': expr_form}
        kwargs.update(self._credentials)
        minions = self._client.cmd(target, 'grains.items', (), **kwargs)
        return [Minion(grains) for id_, grains in minions.iteritems()]

    def sync_states(self, target='*', expr_form='glob'):
        """
        Runs the salt method saltutil.sync_states on the targeted minions.

        @param target: Minion target
        @param expr_form: How to target minions
        @return: Dict describing which custom states were synced

        """
        kwargs = {
            'expr_form': expr_form,
            'arg': (),
        }        
        kwargs.update(self._credentials)
        result = self._client.cmd(target, 'saltutil.sync_states', **kwargs)
        return result        

    def set_roles(self, minions, roles=None):
        """
        Sets the roles value of the specified minions' grains and then updates
        the minion objects with the results
        
        @param minions: List of minions to set roles for
        @param roles: List of roles to set roles to.  Leave None to remove
                      roles.

        """
        if roles is None:
            roles = []
        elif isinstance(roles, basestring):
            roles = [roles]

        if isinstance(minions, Minion):
            minions = [minions]

        func_args = ('roles', roles)
        target = ','.join([minion.id_ for minion in minions])
        kwargs = {
            'expr_form': 'list',
            'arg': func_args
        }
        
        kwargs.update(self._credentials)
        updates = self._client.cmd(target, 'grains.setval', **kwargs)
        for minion in minions:
            if minion.id_ in updates:
                minion.update(updates[minion.id_])

    def apply_state(self, minions, state):
        """
        Applies the state to the specified minions.
        Sync_states is called before state.sls.
        @TODO make timeout changeable

        @param minions: List of minions to apply the state to
        @param state: String indicating which state to use
        @return @TODO

        """    
        if isinstance(minions, Minion):
            minions = [minions]

        target = ','.join([minion.id_ for minion in minions])

        self.sync_states(target=target, expr_form='list')

        kwargs = {
            'timeout': 120,
            'expr_form': 'list',
            'arg': (state,)
        }
        kwargs.update(self._credentials)
        response = self._client.cmd(target, 'state.sls', **kwargs)
        self.check_state_response(state, response)
        return response

    def check_state_response(self, state, response):
        """
        Checks the result of a call to state.sls

        @param state_result: Dict describing the result of a call to state.sls
        """
        failures = []
        for minion_id, minion_response in response.iteritems():
            if isinstance(minion_response, list):
                failures.append(minion_response)
            else:
                for state_key, state_result in minion_response.iteritems():
                    if not state_result.get('result'):
                        state_name, sls_id, name, func = state_key.split('_|-')
                        failures.append((minion_id, sls_id, state_name, name, func, state_result.get('comment')))

        if len(failures) > 0:
            raise SaltStateException(state, failures)

    def cmd(self, target, func, **kwargs):
        kwargs.update(self._credentials)
        return self._client.cmd(target, func, **kwargs)

    def job(self, target, func, **kwargs):
        kwargs.update(self._credentials)
        return self._client.run_job(target, func, **kwargs)

    def get_pillar(self, minions, what, default=None, **kwargs):
        return self.get_pillar_or_grains('pillar.get', minions, what, default, **kwargs)

    def get_grains(self, minions, what, default=None, **kwargs):
        return self.get_pillar_or_grains('grains.get', minions, what, default, **kwargs)

    def get_pillar_or_grains(self, method, minions, what, default, **kwargs):
        
        if isinstance(minions, Minion):
            minions = [minions]
        target = ','.join([m.id_ for m in minions])
        kwargs.update(self._credentials)
        kwargs.update({
            'arg': (what, default),
            'expr_form': 'list'
        })
        ret = self._client.cmd(target, method, **kwargs)
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
        if isinstance(minions, Minion):
            minions = [minions]
        target = [m.id_ for m in minions]

        kwargs.update(self._credentials)
        kwargs.update({'arg': ('interfaces:%s' % interface, default_interface)})
        kwargs.update({'expr_form': 'list'})

        # Get interfaces keyed by minion id
        interface_dict = self._client.cmd(target, 'pillar.get', **kwargs)

        # If there is only one interface, then we can get away with one salt call
        # for the ip address
        unique_interfaces = set([i for minion_id, i in interface_dict.iteritems()])
        if len(unique_interfaces) == 1:
            kwargs.update({'arg': (unique_interfaces.pop(),)})
            ret = self._client.cmd(target, 'network.ipaddrs', **kwargs)

        # Otherwise we have to iterate
        else :
            ret = {}
            for minion_id, interface in interface_dict:
                kwargs.update({'arg': (interface,)})
                ret.update(self._client.cmd(minion_id, 'network.ipaddrs', **kwargs))

        return ret
