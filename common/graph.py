import itertools


class MinionGraph(object):
    """
    Builds a list of nodes and a list of links to be used with a d3 graph
    in javascript.

    """
    def __init__(self, minions, edge_map):
        """
        Initializes the d3 Force graph

        @param minions - List of minions
        @param edge_map - Dict representing a mapping of edges from minions
            with role key to minions with role value

        """
        self.nodes = [self.make_node(m) for m in minions]
        self.links = self.make_links(self.nodes, edge_map)

    def make_node(self, minion):
        """
        Create a graph node

        @param minion - Minion
        @return - Returns a dict representing a graph node with a subset of
            information about the minion

        """
        return {
            'id': minion.id_,
            'os': minion.os,
            'cpu_model': minion.cpu_model,
            'cpu_arch': minion.cpu_arch,
            'num_cpus': minion.num_cpus,
            'memory': minion.memory,
            'roles': minion.data.get('instance_roles', minion.roles)
        }

    def make_links(self, nodes, edge_map):
        """
        Builds a list of links from source nodes to target nodes according to
        the edge map.

        @param nodes - List of minion nodes
        @param edge_map - Dict reprsenting mapping of edges from minions with
            with a source role to a minion with a target role.
        @return - List of links from sources to targets

        """
        links = []
        for source_role, target_roles in edge_map.iteritems():
            pairs = itertools.product(range(len(nodes)), repeat=2)
            for source_index, target_index in pairs:
                for target_role in target_roles:
                    if source_role in nodes[source_index]['roles'] \
                            and target_role in nodes[target_index]['roles']:
                        links.append({
                            'source': nodes[source_index]['id'],
                            'target': nodes[target_index]['id']
                        })
        return links
