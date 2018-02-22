import math
import networkx as nx
import asyncio
from utils.data_structures import StackSet


def _get_greatest_edge_in_bunch(edge_bunch, weight='weight'):
    """
    Edge bunch must be of the format (u, v, d) where u and v are the tail and head nodes (respectively) and d is a list
    of dicts holding the edge_data for each edge in the bunch
    
    Not optimized because currently the only place that calls it first checks len(edge_bunch[2]) > 0
    todo: could take only edge_bunch[2] as parameter
    todo: not needed here, could send put in wardbradt/networkx
    """
    if len(edge_bunch[2]) == 0:
        raise ValueError("Edge bunch must contain more than one edge.")
    greatest = {weight: -float('Inf')}
    for data in edge_bunch[2]:
        if data[weight] > greatest[weight]:
            greatest = data
            
    return greatest


def _get_least_edge_in_bunch(edge_bunch, weight='weight'):
    """
    Edge bunch must be of the format (u, v, d) where u and v are the tail and head nodes (respectively) and d is a list
    of dicts holding the edge_data for each edge in the bunch

    todo: add this to some sort of utils file/ module in wardbradt/networkx
    """
    if len(edge_bunch[2]) == 0:
        raise ValueError("Edge bunch must contain more than one edge.")
    
    least = {weight: float('Inf')}
    for data in edge_bunch[2]:
        if data[weight] < least[weight]:
            least = data

    return least


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
        # self.predecessor is a dict keyed by node and valued by lists which serve as priority queues. see this link:
        # https://docs.python.org/3/tutorial/datastructures.html#using-lists-as-queues to understand how they do so.
        # look at the comment in _retrace_negative_loop_t to understand the elements in each pqueue (list).
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
        [self._process_edge_bunch(edge_bunch) for edge_bunch in self.graph.edge_bunches(data=True)]

    def _process_edge_bunch(self, edge_bunch):
        ideal_edge = _get_least_edge_in_bunch(edge_bunch)
        # todo: does this ever happen?
        if ideal_edge['weight'] == float('Inf'):
            print("happened")
            return

        # todo: there is probably a more efficient way to keep only the edges which show minimum ask and maximum bid
        self.new_graph.add_edge(edge_bunch[0], edge_bunch[1],
                                exchange_name=ideal_edge['exchange_name'],
                                market_name=ideal_edge['market_name'],
                                weight=ideal_edge['weight'])

        if self.distance_to[edge_bunch[0]] + ideal_edge['weight'] <= self.distance_to[edge_bunch[1]]:
            self.distance_to[edge_bunch[1]] = self.distance_to[edge_bunch[0]] + ideal_edge['weight']
            self.predecessor[edge_bunch[1]].add(edge_bunch[0])
            # self.predecessor[edge_bunch[1]].append(edge_bunch[0])

    def bellman_ford(self, source):
        """
        todo: would be very easy to refactor this to accommodate plain digraphs.

        :param source: The node in graph from which the values in distance_to will be calculated.
        :return: a 2-tuple containing the graph with least weighted edges in each edge bunch and the path for a
        negative cycle through that graph
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

        yield self.new_graph
        for edge in self.new_graph.edges(data=True):
            if self.distance_to[edge[0]] + edge[2]['weight'] < self.distance_to[edge[1]]:
                # print_profit_opportunity_for_path(self.new_graph, _retrace_negative_loop_t(self.predecessor, edge[0]))

                yield _retrace_negative_loop_t(self.predecessor, edge[1])

        return self.new_graph, []


def _retrace_negative_loop(predecessor, start):
    """
    Does not currently work as a node may be encountered more than once.
    """
    arbitrage_loop = [start]
    next_node = start
    while True:
        next_node = predecessor[next_node]

        if next_node not in arbitrage_loop:
            arbitrage_loop.insert(0, next_node)
        else:
            arbitrage_loop.insert(0, next_node)
            # arbitrage_loop = arbitrage_loop[arbitrage_loop.index(next_node):]
            return arbitrage_loop


def _retrace_negative_loop_t(predecessor, start):
    """
    In development.
    :param predecessor: A dict keyed by node n1 and valued by priority queues of preceding nodes (the node n2 at top
    of each queue has least weighted edge n2 -> n1 in stack. queue should be in ascending order of edge weights).
    :param start: the node at which the cycle starts
    :return: negative loop path
    """
    arbitrage_loop = [start]
    next_node = start
    while True:
        # if arbitrage_loop[0] has a predecessor (if the loop is incomplete)
        if not predecessor[next_node].done_popping:
            next_node = predecessor[next_node].soft_pop()
            arbitrage_loop.insert(0, next_node)
        # else, loop is finished.
        else:
            for stack_set in predecessor.values():
                stack_set.soft_pop_counter = 0
            # return arbitrage_loop[arbitrage_loop.index(start):]
            return arbitrage_loop


def bellman_ford_multi(graph: nx.MultiGraph, source):
    return NegativeWeightFinderMulti(graph).bellman_ford(source)


def calculate_profit_for_path_multi(graph: nx.MultiGraph, path):
    total = 0
    for i in range(len(path)):
        if i + 1 < len(path):
            start = path[i]
            end = path[i + 1]
            # x and y serve no purpose, they are for debugging.
            # x = graph[start]
            # y = x[end][0]
            total += graph[start][end]['weight']

    return total


def print_profit_opportunity_for_path(graph: nx.Graph, path):
    if not path:
        return

    money = 100
    print("Starting with %(money)i in %(currency)s" % {"money": money, "currency": path[0]})

    for i in range(len(path)):
        if i + 1 < len(path):
            start = path[i]
            end = path[i + 1]
            # x and y serve no purpose, they are for debugging.
            # x = graph[start]
            # y = x[end][0]
            rate = math.exp(-graph[start][end]['weight'])
            money *= rate
            print("{} to {} at {} = {} on {} for {}".format(start, end, rate, money,
                                                            graph[start][end]['exchange_name'],
                                                            graph[start][end]['market_name']))
