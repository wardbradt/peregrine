import math
import networkx as nx
from utils import last_index_in_list, PrioritySet, next_to_each_other


class SeenNodeError(Exception):
    pass


class NegativeWeightFinder:

    def __init__(self, graph: nx.Graph):
        self.graph = graph
        self.predecessor_to = {}
        self.distance_to = {}
        self.predecessor_from = {}
        self.distance_from = {}

        self.seen_nodes = set()
    
    def initialize(self, source):
        for node in self.graph:
            # Initialize all distance_to values to infinity and all predecessor_to values to None
            self.distance_to[node] = float('Inf')
            self.predecessor_to[node] = PrioritySet()
            self.distance_from[node] = float('Inf')
            self.predecessor_from[node] = PrioritySet()

        # The distance from any node to (itself) == 0
        self.distance_to[source] = 0
        self.distance_from[source] = 0

    def bellman_ford(self, source, loop_from_source=True, ensure_profit=False, unique_paths=False):
        """
        Note: the loop_from_source parameter, when set to True, currently outputs a less than ideal path from source
        to the beginning of the arbitrage opportunity.
        
        :param ensure_profit: if true, ensures that the weight of the returned path is greater able to be arbitraged
        for a profit. if false, the resultant path may not be profitable because although it contains a negative cycle
        (arbitrage-able loop), the weight of the paths to and from that cycle are more positive than the absolute value
        of the negative cycle, rendering the path as a whole positive. Still in development, does not currently work.
        :param loop_from_source: if true, will return the path beginning and ending at source. Note: this may cause the
        path to be a positive-weight cycle (if traversed straight through). Because a negative cycle exists in the path,
        (and it can be traversed infinitely many times), the path is negative. This is still in development and is
        certainly not optimized. It is not an implementation of an algorithm that I know of but one that I have created
        (without too much weight on the optimization, more so on simply completing it).
        :param source: The node in graph from which the values in distance_to and distance_from will be calculated.
        """
        self.initialize(source)
        # After len(graph) - 1 passes, algorithm is complete.
        for i in range(len(self.graph) - 1):
            # for each node in the graph, test if the distance to each of its siblings is shorter by going from
            # source->base_currency + base_currency->quote_currency
            for edge in self.graph.edges(data=True):
                self.relax(edge)

        for edge in self.graph.edges(data=True):
            if self.distance_to[edge[0]] + edge[2]['weight'] < self.distance_to[edge[1]]:
                try:
                    yield self._retrace_negative_loop(edge[1],
                                                      loop_from_source=loop_from_source,
                                                      source=source,
                                                      ensure_profit=ensure_profit,
                                                      unique_paths=unique_paths)
                except SeenNodeError:
                    continue

    def relax(self, edge):
        if self.distance_to[edge[0]] + edge[2]['weight'] < self.distance_to[edge[1]]:
            self.distance_to[edge[1]] = self.distance_to[edge[0]] + edge[2]['weight']

        # todo: there must be a more efficient way to order neighbors by preceding path weights
        # no matter what, adds this edge to the PrioritySet in distance_to
        self.predecessor_to[edge[1]].add(edge[0], self.distance_to[edge[0]] + edge[2]['weight'])

        if self.distance_from[edge[1]] + edge[2]['weight'] < self.distance_from[edge[0]]:
            self.distance_from[edge[0]] = self.distance_from[edge[1]] + edge[2]['weight']

        self.predecessor_from[edge[0]].add(edge[1],
                                           self.distance_from[edge[1]] + edge[2]['weight'])

        return True

    def _retrace_negative_loop(self, start, loop_from_source=False, source='', ensure_profit=False, unique_paths=False):
        """
        @:param loop_from_source: look at docstring of bellman_ford
        :return: negative loop path
        """
        if unique_paths and start in self.seen_nodes:
            raise SeenNodeError

        arbitrage_loop = [start]
        # todo: could refactor to make the while statement `while next_node not in arbitrage_loop`
        if not loop_from_source:
            next_node = start
            while True:
                next_node = self.predecessor_to[next_node].pop()[1]
                # if negative cycle is complete
                if next_node in arbitrage_loop:
                    arbitrage_loop = arbitrage_loop[:last_index_in_list(arbitrage_loop, next_node) + 1]
                    arbitrage_loop.insert(0, next_node)
                    self.reset_predecessor_iteration()
                    return arbitrage_loop

                # if next_node in arbitrage_loop, next_node in self.seen_nodes. thus, this conditional must proceed
                # checking if next_node in arbitrage_loop
                if unique_paths and next_node in self.seen_nodes:
                    raise SeenNodeError(next_node)

                arbitrage_loop.insert(0, next_node)
                self.seen_nodes.add(next_node)
        else:
            if source not in self.graph:
                raise ValueError("source not in graph.")

            # todo: i do not remember to which edge case this refers, test to see which then specify in the comment.
            # adding the predecessor to start to arbitrage loop outside the while loop prevents an edge case.
            next_node = self.predecessor_to[arbitrage_loop[0]].peek()[1]
            if unique_paths and next_node in self.seen_nodes:
                raise SeenNodeError(next_node)

            arbitrage_loop.insert(0, next_node)

            # todo: refactor this so it is not while True, instead while not next_to_each_other
            while True:
                next_node = self.predecessor_to[arbitrage_loop[0]].peek()[1]

                # if this edge has been traversed over, negative cycle is complete.
                if next_to_each_other(arbitrage_loop, next_node, arbitrage_loop[0]):
                    arbitrage_loop.insert(0, next_node)
                    arbitrage_loop = arbitrage_loop[:last_index_in_list(arbitrage_loop, next_node) + 1]

                    if ensure_profit:
                        # todo: is this inefficient because it iterates over arbitrage_loop twice? once to check if in,
                        # once to get index?
                        if source in arbitrage_loop:
                            index = arbitrage_loop.index(source)
                            arbitrage_loop = arbitrage_loop[index:] + arbitrage_loop[:index]

                        # the weight of the path that will be taken to make arbitrage_loop start and end at source
                        return_path_weight = self.distance_to[arbitrage_loop[0]] + self.distance_from[arbitrage_loop[-1]]
                        loop_weight = 0
                        if return_path_weight > 0:
                            # todo: this is not the most efficient way to get the weight of arbitrage_loop
                            for i in range(len(arbitrage_loop) - 1):
                                loop_weight += self.graph[arbitrage_loop[i]][arbitrage_loop[i + 1]]['weight']

                            scalar = return_path_weight / abs(loop_weight) + 1
                            if scalar.is_integer():
                                scalar += 1
                            else:
                                scalar = math.ceil(scalar)

                            arbitrage_loop *= scalar

                    self.predecessor_to[arbitrage_loop[0]].pop()

                    def _pop_arbitrage_loop(loop, predecessor):
                        while predecessor[loop[0]].empty:
                            loop.pop(0)

                    # add the path from source -> min_distance_to_node to the beginning of arbitrage_loop
                    while arbitrage_loop[0] != source:
                        _pop_arbitrage_loop(arbitrage_loop, self.predecessor_to)
                        next_node = self.predecessor_to[arbitrage_loop[0]].pop()[1]
                        # if this edge has already been traversed over/ added to arbitrage_loop, must exit the cycle.
                        if next_to_each_other(arbitrage_loop, next_node, arbitrage_loop[0]):
                            self.predecessor_to[arbitrage_loop[0]].pop()
                            # this prevents an error where every edge from a node has been traversed over.
                            _pop_arbitrage_loop(arbitrage_loop, self.predecessor_to)

                            next_node = self.predecessor_to[arbitrage_loop[0]].pop()[1]

                        arbitrage_loop.insert(0, next_node)

                    # add the path from arbitrage_loop[-1] -> source to the end of arbitrage_loop
                    while arbitrage_loop[-1] != source:
                        next_node = self.predecessor_from[arbitrage_loop[-1]].peek()[1]
                        if next_to_each_other(arbitrage_loop, arbitrage_loop[-1], next_node):
                            self.predecessor_from[arbitrage_loop[-1]].pop()

                        arbitrage_loop.append(next_node)

                    self.reset_predecessor_iteration()
                    return arbitrage_loop

                else:
                    if unique_paths and next_node in self.seen_nodes:
                        raise SeenNodeError(next_node)

                    arbitrage_loop.insert(0, next_node)
                    self.seen_nodes.add(next_node)

    def reset_predecessor_iteration(self):
        for node in self.predecessor_to.keys():
            self.predecessor_to[node].reset()
            # predecessor_to and predecessor_to have the same keys
            self.predecessor_from[node].reset()


def bellman_ford(graph, source, loop_from_source=True, ensure_profit=False, unique_paths=False):
    """
    Look at the docstring of the bellman_ford method in the NegativeWeightFinder class as this is a wrapper method.
    """
    return NegativeWeightFinder(graph).bellman_ford(source, loop_from_source, ensure_profit, unique_paths=unique_paths)


def calculate_profit_ratio_for_path(graph, path):
    total = 0
    for i in range(len(path)):
        if i + 1 < len(path):
            start = path[i]
            end = path[i + 1]
            total += graph[start][end]['weight']

    return math.exp(-total)
