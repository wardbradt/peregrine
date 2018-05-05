import networkx as nx
from .bellmannx import NegativeWeightFinder, SeenNodeError
from .utils import get_least_edge_in_bunch


class NegativeWeightFinderMulti(NegativeWeightFinder):

    def __init__(self, graph: nx.MultiGraph):
        super(NegativeWeightFinderMulti, self).__init__(graph)
        self.new_graph = nx.DiGraph()

    def bellman_ford(self, source, loop_from_source=True, ensure_profit=False, unique_paths=False):
        self.initialize(source)

        # on first iteration, load market prices.
        self._first_iteration()

        # After len(graph) - 1 passes, algorithm is complete.
        for i in range(1, len(self.graph) - 1):
            for edge in self.new_graph.edges(data=True):
                self.relax(edge)

        for edge in self.new_graph.edges(data=True):
            # todo: does this indicate that there is a negative cycle beginning and ending with edge[1]? or just that
            # edge[1] connects to a negative cycle?
            if self.distance_to[edge[0]] + edge[2]['weight'] < self.distance_to[edge[1]]:
                try:
                    yield self._retrace_negative_loop(edge[1],
                                                      loop_from_source=loop_from_source,
                                                      source=source,
                                                      ensure_profit=ensure_profit,
                                                      unique_paths=unique_paths)
                except SeenNodeError:
                    continue

    def _first_iteration(self):
        """
        On the first iteration, finds the least-weighted edge between in each edge bunch in self.graph and creates
        a DiGraph, self.new_graph using those least-weighted edges. Also completes the first relaxation iteration. This
        is why in bellman_ford, there are only len(self.graph) - 1 iterations of relaxing the edges. (The first
        iteration is completed in the method.)
        """
        [self._process_edge_bunch(edge_bunch) for edge_bunch in self.graph.edge_bunches(data=True)]

    def _process_edge_bunch(self, edge_bunch):
        ideal_edge = get_least_edge_in_bunch(edge_bunch)
        # todo: does this ever happen? if so, the least weighted edge in edge_bunch would have to be of infinite weight
        if ideal_edge['weight'] == float('Inf'):
            return

        self.new_graph.add_edge(edge_bunch[0], edge_bunch[1], **ideal_edge)

        # todo: these conditionals are rarely both true. how to detect when this is the case?
        if self.distance_to[edge_bunch[0]] + ideal_edge['weight'] < self.distance_to[edge_bunch[1]]:
            self.distance_to[edge_bunch[1]] = self.distance_to[edge_bunch[0]] + ideal_edge['weight']
        self.predecessor_to[edge_bunch[1]].add(edge_bunch[0],
                                               self.distance_to[edge_bunch[0]] + ideal_edge['weight'])

        if self.distance_from[edge_bunch[1]] + ideal_edge['weight'] < self.distance_from[edge_bunch[0]]:
            self.distance_from[edge_bunch[0]] = self.distance_from[edge_bunch[1]] + ideal_edge['weight']
        self.predecessor_from[edge_bunch[0]].add(edge_bunch[1],
                                                 self.distance_from[edge_bunch[1]] + ideal_edge['weight'])


def bellman_ford_multi(graph: nx.MultiGraph, source, loop_from_source=False, ensure_profit=False, unique_paths=False):
    """
    Returns a 2-tuple containing the graph with most negative weights in every edge bunch and a generator which iterates
    over the negative cycle in graph
    """
    finder = NegativeWeightFinderMulti(graph)
    paths = finder.bellman_ford(source, loop_from_source=loop_from_source, ensure_profit=ensure_profit,
                                unique_paths=unique_paths)
    return finder.new_graph, paths
