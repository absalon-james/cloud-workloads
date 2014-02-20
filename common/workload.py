import pprint

class Workload(object):
    """
    Class that handles a cloud workload.  A workload should consist
    of necessary tools to install, run, and parse output.

    Configuration should go in self.config
    Data collected during execution should go into self.data
    """

    # Default roles to states mapping
    DEFAULT_STATES = {}

    # Default roles to anti-states mapping
    DEFAULT_ANTI_STATES = {}

    # Default configuration
    DEFAULT_CONFIG = {}

    def __init__(self, client, pool, config):
        """
        Initializes the workload. Updates the configuration with defaults
        and then the configuration passed in via the config argument.

        @param client - Salt local client
        @param pool - MinionPool
        @param config - Workload configuration dictionary

        """
        self.is_primitive = False
        self.client = client
        self.pool = pool
        self.config = {}
        self.config.update(self.DEFAULT_CONFIG)
        self.config.update(config)

    def deploy(self):
        """
        Requests minions from minion pool, applies roles to the minions, and
        then applies salt states to the minions.
 
        """
        self.get_minions()
        self.apply_roles()
        self.apply_states()
        return True

    def undeploy(self):
        """
        Undeploys the workload. Applies anti-states to minions. Removes added
        roles from minions. Returns minions to the minion pool.

        """
        try:
            self.remove_states()
            self.remove_roles()
            self.return_minions()
        except Exception, e:
            print "Something happened while undeploying"
            print e
            # TODO some sort of warning or log for when undeploy fails.
            return False
        return True

    def minions_with_role(self, role):
        """
        Convenience method for grabbing all minions with the requested role.

        @param role - String role
        @return List of minions
        """
        return [i['minion'] for i in self.instances if role in i['minion'].roles]
        

    def get_minions(self):
        """
        Gets minions from the minion pool and attaches instance information
        that should be tracked throughout the workload.

        """
        self.instances = []
        instances = self.config.get('instances', [])
        for i in instances:
            roles = set(i['roles'])
            minion = self.pool.get_minion()
            instance = {'minion': minion}
            instance.update(i)

            if not 'states' in instance:
                instance['states'] = set()
                for role in roles:
                    states = self.DEFAULT_STATES.get(role, [])
                    instance['states'].update(states)
                    
            if not 'antistates' in instance:
                instance['antistates'] = set()
                for role in roles:
                    antistates = self.DEFAULT_ANTI_STATES.get(role, [])
                    instance['antistates'].update(antistates)

            self.instances.append(instance)
 
    def apply_roles(self):
        """
        Applies roles to each minion according to its instance.
        Roles listed in the instance are added to the existing roles of
        the minion.

        """
        minion_sets = []
        role_sets = []
        for instance in self.instances:
            minion = instance.get('minion')
            roles = set(minion.roles or [])
            for role in instance.get('roles', []):
                roles.add(role)
            roles = list(roles)
            minion_sets.append([minion])
            role_sets.append(roles)
        self.client.set_roles(minion_sets, role_sets, timeout=30)

    def deploy_plan(self, deploy=True):
        if deploy:
            deploy_sequence = self.DEPLOY_SEQUENCE
            states_key = 'states'
            
        else:
            deploy_sequence = self.UNDEPLOY_SEQUENCE
            states_key = 'antistates'
        cmds = []
        for sequence in deploy_sequence:
            chain = None
            while True:
                state = sequence['state']
                minions = []
                for instance in self.instances:
                    if state in instance[states_key]:
                        minions.append(instance['minion'])
                cmd = self.client.prepare_cmd_state(minions, state, sync=True)
                if chain:
                    chain.link(cmd)
                else:
                    chain = cmd
                if not sequence.has_key('next'):
                    break
                sequence = sequence['next']
            cmds.append(chain)
        return cmds

    def apply_states(self):
        """
        Applies states to the minions as decribed by each minion's instance.

        """

        cmds = self.deploy_plan()
        resp = self.client.run_multi(cmds)
        # TODO - validate the response

        #print "Applying states ..."
        #for instance in self.instances:
        #    minion = instance.get('minion')
        #    for state in instance.get('states', []):
        #        print "'%s' to %s" % (state, minion.id_)
        #        result = self.client.apply_state(minion, state)

    def remove_states(self):
        """
        Applies antistates to each minion as described by each minion's
        instance.

        """
        cmds = self.deploy_plan(deploy=False)
        resp = self.client.run_multi(cmds)
        #print "Removing states ..."
        #for instance in self.instances:
        #    minion = instance.get('minion')
        #    for state in instance.get('antistates', []):
        #        try:
        #            print "'%s' to %s" % (state, minion.id_)
        #            result = self.client.apply_state(minion, state)
        #        except Exception as e:
        #            print e
                

    def remove_roles(self):
        """
        Returns minion roles to what they were prior to this workload.
        Roles used in an instance are removed from the instance.

        """
        minion_sets = []
        role_sets = []
        for instance in self.instances:
            minion = instance.get('minion')
            roles = set(minion.roles or [])
            for role in instance.get('roles', []):
                if role in roles:
                    roles.remove(role)
            roles = list(roles)            
            role_sets.append(roles)
            minion_sets.append([minion])
        self.client.set_roles(minion_sets, role_sets, timeout=30)

    def return_minions(self):
        """
        Returns the now unused minions back to the minion pool.

        """
        for instance in self.instances:
            minion = instance.get('minion')
            if minion is not None:
                self.pool.put_minion(minion)       

    def run(self):
        """Runs the workload"""
        pass

    def view(self):
        """
        Should return a string view of this workload.  The string should be
        valid html that can be dumped with other html.

        :returns: String html representation of workload output
        """
        return "missing view method"

    @property
    def name(self):
        """
        Returns the name of the workload.

        :returns: String name of the workload
        """
        return "missing name property"
