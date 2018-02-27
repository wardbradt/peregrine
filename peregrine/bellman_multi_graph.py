import math
import networkx as nx
from utils import StackSet, last_index_in_list, get_least_edge_in_bunch


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
        # Although the StackSet functionality is not currently used, it may be useful in the future (particularly if
        # attempting to exit a predecessor cycle)
        self.predecessor = {}
        self.distance_to = {}

    def initialize(self, source):
        for node in self.graph:
            # Initialize all distance_to values to infinity and all predecessor values to None
            self.distance_to[node] = float('Inf')
            self.predecessor[node] = StackSet()
        # The distance from any node to (itself) == 0
        self.distance_to[source] = 0

    def _first_iteration(self):
        """
        On the first iteration, finds the least-weighted edge between in each edge bunch in self.graph and creates
        a DiGraph, self.new_graph using those least-weighted edges. Also completes the first relaxation iteration. This
        is why in bellman_ford, there are only len(self.graph) - 1 iterations of relaxing the edges. (The first
        iteration is completed in the method.)
        """
        [self._process_edge_bunch(edge_bunch) for edge_bunch in self.graph.edge_bunches(data=True)]

    def _process_edge_bunch(self, edge_bunch):
        """
        todo: could easily refactor this for general usage. (e.g. not specifically for graphs with exchange_name
        and market_name edge attributes
        """
        ideal_edge = get_least_edge_in_bunch(edge_bunch)
        # todo: does this ever happen? if so, the least weighted edge in edge_bunch would have to have infinite weight
        if ideal_edge['weight'] == float('Inf'):
            return

        self.new_graph.add_edge(edge_bunch[0], edge_bunch[1], **ideal_edge)

        if self.distance_to[edge_bunch[0]] + ideal_edge['weight'] <= self.distance_to[edge_bunch[1]]:
            self.distance_to[edge_bunch[1]] = self.distance_to[edge_bunch[0]] + ideal_edge['weight']
            self.predecessor[edge_bunch[1]].add(edge_bunch[0])

    def bellman_ford(self, source, loop_from_source=False):
        """
        todo: would be very easy to refactor this to accommodate plain digraphs.
        :param loop_from_source: if true, will return the path beginning and ending at source. Note: this may cause the
        path to be a positive-weight cycle (if traversed straight through). Because a negative cycle exists in the path,
        (and it can be traversed infinitely many times), the path is negative.
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
                    # important todo: there must be a more efficient way to order neighbors by preceding path weights
                    # move edge[0] to the end of self.predecessor[edge[1]]
                    self.predecessor[edge[1]].add(edge[0])

        # todo: to find all edges, refactor this for loop. don't use edges. i believe that for every node, if
        # self.distance_to[edge[0]] + edge[2]['weight'] < self.distance_to[edge[1]] and this function yields on that
        # iteration, it returns the same path accessible from edge[0]
        for edge in self.new_graph.edges(data=True):
            # todo: does this indicate that there is a negative cycle beginning and ending with edge[1]? or just that
            # edge[1] connects to a negative cycle?
            if self.distance_to[edge[0]] + edge[2]['weight'] < self.distance_to[edge[1]]:
                # todo: does relaxing the edge ensure that the starting and ending nodes are source if source is in the
                # path?
                self.distance_to[edge[1]] = self.distance_to[edge[0]] + edge[2]['weight']
                self.predecessor[edge[1]].add(edge[0])
                yield self._retrace_negative_loop(edge[1], loop_from_source, source)
                self.reset_predecessor_iteration()

        # return self.new_graph, []

    def _retrace_negative_loop(self, start, loop_from_source=False, source=''):
        """
        @:param loop_from_source: look at docstring of bellman_ford
        :return: negative loop path
        """
        arbitrage_loop = [start]
        next_node = start
        # todo: could refactor to make the while statement `while next_node not in arbitrage_loop`
        if not loop_from_source:
            while True:
                next_node = self.predecessor[next_node].soft_pop()
                if next_node not in arbitrage_loop:
                    arbitrage_loop.insert(0, next_node)
                # else, negative cycle is complete.
                else:
                    arbitrage_loop.insert(0, next_node)
                    arbitrage_loop = arbitrage_loop[:last_index_in_list(arbitrage_loop, next_node) + 1]
                    return arbitrage_loop
        else:
            while True:
                next_node = self.predecessor[next_node].soft_pop()
                if next_node not in arbitrage_loop:
                    arbitrage_loop.insert(0, next_node)
                # else, negative cycle is complete.
                else:
                    arbitrage_loop = arbitrage_loop[:last_index_in_list(arbitrage_loop, next_node) + 1]
                    # the node in arbitrage_loop which has the least weighted path to source
                    min_distance_node = min(arbitrage_loop, key=lambda x: self.distance_to[x])
                    # todo: collections.deque might be more efficient for shifting the list. might not be because would
                    # probably necessitate call to .index()
                    # rotate so that min_distance_node is first in arbitrage_loop
                    for i in range(len(arbitrage_loop)):
                        if arbitrage_loop[0] != min_distance_node:
                            arbitrage_loop = arbitrage_loop[1:] + arbitrage_loop[0]
                        else:
                            break
                    arbitrage_loop.append(min_distance_node)
                    # todo: is there an edge case if source is in arbitrage_loop?
                    while next_node != source:
                        pass

                    return arbitrage_loop

    def _retrace_negative_loops(self, start):
        pass

    def reset_predecessor_iteration(self):
        for node in self.predecessor.keys():
            self.predecessor[node].soft_pop_counter = 0


def bellman_ford_multi(graph: nx.MultiGraph, source):
    """
    Returns a 2-tuple containing the graph with most negative weights in every edge bunch and a generator which iterates
    over the negative cycle in graph
    """
    finder = NegativeWeightFinderMulti(graph)
    paths = finder.bellman_ford(source)
    return finder.new_graph, paths


def calculate_profit_for_path_multi(graph: nx.MultiGraph, path):
    total = 0
    for i in range(len(path)):
        if i + 1 < len(path):
            start = path[i]
            end = path[i + 1]
            total += graph[start][end]['weight']

    return math.exp(-total)


