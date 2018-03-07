import math
import networkx as nx
from utils import last_index_in_list, get_least_edge_in_bunch, PrioritySet, next_to_each_other


class NegativeWeightFinderMulti:

    def __init__(self, graph: nx.MultiGraph):
        """
        Currently takes a non weighted MultiGraph representing a group of exchanges
        (as formatted in create_multi_exchange_graph)
        """
        self.graph = graph
        # Because cannot modify graph's edges while iterating over its edge_bunches, must create new graph
        # graph with lowest ask and highest bid
        self.new_graph = nx.DiGraph()
        # A dict keyed by node n1 and valued by StackSets of preceding nodes (the node n2 at top
        # of each queue has least weighted edge n2 -> n1 in stack. queue should be in ascending order of edge weights).
        self.predecessor_to = {}
        self.distance_to = {}
        self.predecessor_from = {}
        self.distance_from = {}

    def initialize(self, source):
        for node in self.graph:
            # Initialize all distance_to values to infinity and all predecessor values to None
            self.distance_to[node] = float('Inf')
            self.predecessor_to[node] = PrioritySet()
            self.distance_from[node] = float('Inf')
            self.predecessor_from[node] = PrioritySet()
        # The distance from any node to itself == 0
        self.distance_to[source] = 0
        self.distance_from[source] = 0

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

        if self.distance_to[edge_bunch[0]] + ideal_edge['weight'] < self.distance_to[edge_bunch[1]]:
            self.distance_to[edge_bunch[1]] = self.distance_to[edge_bunch[0]] + ideal_edge['weight']
        self.predecessor_to[edge_bunch[1]].add(edge_bunch[0],
                                               self.distance_to[edge_bunch[0]] + ideal_edge['weight'])

        # todo: these conditionals are rarely both true. how to detect when this is the case?
        if self.distance_from[edge_bunch[1]] + ideal_edge['weight'] < self.distance_from[edge_bunch[0]]:
            self.distance_from[edge_bunch[0]] = self.distance_from[edge_bunch[1]] + ideal_edge['weight']
        self.predecessor_from[edge_bunch[0]].add(edge_bunch[1],
                                                 self.distance_from[edge_bunch[1]] + ideal_edge['weight'])

    def bellman_ford(self, source, loop_from_source=False):
        """
        todo: would be very easy to refactor this to accommodate plain digraphs.
        :param loop_from_source: if true, will return the path beginning and ending at source. Note: this may cause the
        path to be a positive-weight cycle (if traversed straight through). Because a negative cycle exists in the path,
        (and it can be traversed infinitely many times), the path is negative. This is still in development and is
        certainly not optimized. It is not an implementation of an algorithm that I know of but one that I have created
        (without too much weight on the optimization, more so on simply completing it).
        todo: loop_from_source would work better (read: for arbitrage) if it was over a multi-exchange multi-graph.
        :param source: The node in graph from which the values in distance_to will be calculated.
        :return: a 2-tuple containing the graph with least weighted edges in each edge bunch and the path for a
        negative cycle through that graph.
        path = [] if no negative weight cycle exists.
        """
        self.initialize(source)

        # on first iteration, load market prices.
        self._first_iteration()

        # After len(graph) - 1 passes, algorithm is complete.
        for i in range(1, len(self.graph) - 1):
            for edge in self.new_graph.edges(data=True):
                if self.distance_to[edge[0]] + edge[2]['weight'] < self.distance_to[edge[1]]:
                    self.distance_to[edge[1]] = self.distance_to[edge[0]] + edge[2]['weight']

                # todo: there must be a more efficient way to order neighbors by preceding path weights
                # no matter what, adds this edge to the PrioritySet in distance_to
                self.predecessor_to[edge[1]].add(edge[0], self.distance_to[edge[0]] + edge[2]['weight'])

                if self.distance_from[edge[1]] + edge[2]['weight'] < self.distance_from[edge[0]]:
                    self.distance_from[edge[0]] = self.distance_from[edge[1]] + edge[2]['weight']

                self.predecessor_from[edge[0]].add(edge[1],
                                                   self.distance_from[edge[1]] + edge[2]['weight'])

        for edge in self.new_graph.edges(data=True):
            # todo: does this indicate that there is a negative cycle beginning and ending with edge[1]? or just that
            # edge[1] connects to a negative cycle?
            if self.distance_to[edge[0]] + edge[2]['weight'] < self.distance_to[edge[1]]:
                # print("data: {} {} {}".format(edge[0], edge[1], str(edge)))
                yield self._retrace_negative_loop(edge[1], loop_from_source=loop_from_source, source=source)

    def _retrace_negative_loop(self, start, loop_from_source=False, source=''):
        """
        @:param loop_from_source: look at docstring of bellman_ford
        :return: negative loop path
        """
        arbitrage_loop = [start]
        # todo: could refactor to make the while statement `while next_node not in arbitrage_loop`
        if not loop_from_source:
            next_node = start
            while True:
                next_node = self.predecessor_to[next_node].pop()[1]
                arbitrage_loop.insert(0, next_node)
                # if negative cycle is complete
                if next_node in arbitrage_loop:
                    arbitrage_loop = arbitrage_loop[:last_index_in_list(arbitrage_loop, next_node) + 1]
                    self.reset_predecessor_iteration()
                    return arbitrage_loop
        else:
            if source not in self.new_graph:
                raise ValueError("source not in graph.")

            while True:
                next_node = self.predecessor_to[arbitrage_loop[0]].peek()[1]
                # if this edge has not been traversed over, add it to arbitrage_loop
                if not next_to_each_other(arbitrage_loop, next_node, arbitrage_loop[0]):
                    arbitrage_loop.insert(0, next_node)
                # else, negative cycle is complete.
                else:
                    arbitrage_loop = arbitrage_loop[:last_index_in_list(arbitrage_loop, next_node) + 1]

                    # add the path from source -> min_distance_to_node to the beginning of arbitrage_loop
                    while arbitrage_loop[0] != source:
                        next_node = self.predecessor_to[arbitrage_loop[0]].peek()[1]
                        # if this edge has already been traversed over/ added to arbitrage_loop, must exit the cycle.
                        if next_to_each_other(arbitrage_loop, next_node, arbitrage_loop[0]):
                            # next_node equals the second least predecessor of arbitrage_loop[0] so as to not reenter a
                            # negative cycle
                            self.predecessor_to[arbitrage_loop[0]].pop()
                            next_node = self.predecessor_to[arbitrage_loop[0]].pop()[1]
                        arbitrage_loop.insert(0, next_node)

                    # add the path from arbitrage_loop[-1] -> source to the end of arbitrage_loop
                    if source == 'REP':
                        print()
                    # while the last element in arbitrage_loop != source
                    while arbitrage_loop[-1] != source:
                        next_node = self.predecessor_from[arbitrage_loop[-1]].peek()[1]
                        if next_to_each_other(arbitrage_loop, arbitrage_loop[-1], next_node):
                            self.predecessor_from[arbitrage_loop[-1]].pop()
                            # next_node equals the second least predecessor of arbitrage_loop[-1] so as to not reenter a
                            # negative cycle
                            # try:
                            #     next_node = self.predecessor_from[arbitrage_loop[-1]].pop()[1]

                        arbitrage_loop.append(next_node)

                    self.reset_predecessor_iteration()
                    return arbitrage_loop

    def _retrace_negative_loops(self, start):
        pass

    def _get_min_distance_from_node(self, path):
        """
        Returns the node n which has the least value for the weight of the path between path[0] and n summed with its
        value in self.distance_from
        """
        if not path:
            raise ValueError

        minimum_node = {'node': path[0], 'return_path_weight': self.distance_from[path[0]]}
        path_weight = 0
        for i in range(1, len(path)):
            start = path[i - 1]
            end = path[i]
            path_weight += self.new_graph[start][end]['weight']
            if self.distance_from[path[i]] + path_weight < minimum_node['return_path_weight']:
                minimum_node['node'] = path[i]
                minimum_node['return_path_weight'] = self.distance_from[path[i]] + path_weight

        return minimum_node['node']

    def reset_predecessor_iteration(self):
        for node in self.predecessor_to.keys():
            self.predecessor_to[node].reset()
            # predecessor_to and predecessor_to have the same keys
            self.predecessor_from[node].reset()


def bellman_ford_multi(graph: nx.MultiGraph, source, loop_from_source=False):
    """
    Returns a 2-tuple containing the graph with most negative weights in every edge bunch and a generator which iterates
    over the negative cycle in graph
    """
    finder = NegativeWeightFinderMulti(graph)
    paths = finder.bellman_ford(source, loop_from_source=loop_from_source)
    return finder.new_graph, paths


def calculate_profit_for_path_multi(graph: nx.MultiGraph, path):
    total = 0
    for i in range(len(path)):
        if i + 1 < len(path):
            start = path[i]
            end = path[i + 1]
            total += graph[start][end]['weight']

    return math.exp(-total)
