import math
import networkx as nx
from .utils import last_index_in_list, PrioritySet, next_to_each_other


class SeenNodeError(Exception):
    pass


class NegativeWeightFinder:

    def __init__(self, graph: nx.Graph, depth=False, starting_amount=1):
        self.graph = graph
        self.predecessor_to = {}
        # the maximum weight which can be transferred from source to each node
        self.distance_to = {}
        self.predecessor_from = {}
        # the maximum weight which can be transferred from each node to source
        self.distance_from = {}

        if depth:
            # equivalent to hasattr(self, 'depth_nodes_to') and hasattr(self, 'depth_nodes_from')
            self.depth = True
            # used only when depth == True in _check_final_condition
            self.starting_amount = starting_amount
            # like distance_to, but accounts for depth
            self.depth_nodes_to = {}
            # like distance_from, but accounts for depth
            self.depth_nodes_from = {}
        else:
            self.depth = False

        self.seen_nodes = set()

    def _set_basic_fields(self, node):
        # Initialize all distance_to values to infinity and all predecessor_to values to None
        self.distance_to[node] = float('Inf')
        self.predecessor_to[node] = PrioritySet()
        self.distance_from[node] = float('Inf')
        self.predecessor_from[node] = PrioritySet()

    def initialize(self, source):
        if self.depth:
            for node in self.graph:
                self._set_basic_fields(node)
                self.depth_nodes_to[node] = 0
        else:
            for node in self.graph:
                self._set_basic_fields(node)

        # The distance from any node to (itself) == 0
        self.distance_to[source] = 0
        self.distance_from[source] = 0

    def bellman_ford(self, source, loop_from_source=False, ensure_profit=False, unique_paths=True):
        """
        Note: the loop_from_source parameter, when set to True, currently outputs a less than ideal path from source
        to the beginning of the arbitrage opportunity.
        :param unique_paths: If true, ensures that no duplicate paths are returned.
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

        return self._check_final_condition(loop_from_source=loop_from_source,
                                           source=source,
                                           ensure_profit=ensure_profit,
                                           unique_paths=unique_paths)

    def _check_final_condition(self, **kwargs):
        """
        NegativeWeightFinder and its children execute the Bellman-Ford algorithm or some variation of it. A main
        variation among the classes is the "final condition," which typically checks whether or not a negative cycle
        exists using that class's specific parameters. If the final condition is true, _check_final_condition returns
        a generator which should yield paths in self.graph.

        For the NegativeWeightFinder class, the final condition is whether or not a negative cycle exists. If this
        condition is true, this method will yield negatively weighted paths.

        All subclasses of NegativeWeightFinder should return a generator of paths which satisfy the final condition. If
        subclassing NegativeWeightFinder and overriding _check_final_condition and planning to publish this subclass, it
        is helpful to describe in the docstring what the final condition is and, if not negative cycles, what the
        method's returned generator yields.
        """
        for edge in self.graph.edges(data=True):
            if self.distance_to[edge[0]] + edge[2]['weight'] < self.distance_to[edge[1]]:
                try:
                    path = self._retrace_negative_loop(edge[1],
                                                       loop_from_source=kwargs['loop_from_source'],
                                                       source=kwargs['source'],
                                                       ensure_profit=kwargs['ensure_profit'],
                                                       unique_paths=kwargs['unique_paths'])
                except SeenNodeError:
                    continue

                if not self.depth:
                    yield path
                # if self.depth, must check that this loop is profitable accounting for depth.
                # todo: this could be optimized to check in _retrace_negative_loop
                else:
                    if calculate_profit_ratio_for_path(self.graph, path, depth=False,
                                                       starting_amount=self.starting_amount) > self.starting_amount:
                        yield path

    def relax(self, edge):
        if self.distance_to[edge[0]] + edge[2]['weight'] < self.distance_to[edge[1]]:
            self.distance_to[edge[1]] = self.distance_to[edge[0]] + edge[2]['weight']
            if self.depth:
                self.depth_nodes_to[edge[1]] = max(self.distance_to[edge[0]], edge[2]['depth']) + edge[2]['weight']

        # todo: there must be a more efficient way to order neighbors by preceding path weights
        # no matter what, adds this edge to the PrioritySet in predecessor_to
        self.predecessor_to[edge[1]].add(edge[0], self.distance_to[edge[0]] + edge[2]['weight'])

        if self.distance_from[edge[1]] + edge[2]['weight'] < self.distance_from[edge[0]]:
            self.distance_from[edge[0]] = self.distance_from[edge[1]] + edge[2]['weight']
            if self.depth:
                self.depth_nodes_from[edge[0]] = max(self.distance_from[edge[1]], edge[2]['depth']) + edge[2]['weight']

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
                        return_path_weight = self.distance_to[arbitrage_loop[0]] + self.distance_from[
                            arbitrage_loop[-1]]
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


class NegativeWeightDepthFinder(NegativeWeightFinder):

    def __init__(self, graph: nx.Graph):
        """
        This variation of NegativeWeightFinder finds the most negative weight cycle including a source node in a
        graph. This varies from setting depth=True in NegativeWeightFinder in the following ways:

        1. NegativeWeightFinder, when depth=True, finds the most negatively weighted cycle while keeping track of
        the weight (or currency) available at each node. After the algorithm has completed, it reveals the negative
        weight accounting for depth of the most negatively-weighted cycle found without accounting for depth. Thus,
        it may return a path which is the most negatively-weighted without accounting for depth but not when accounting
        for depth. However, this version finds the most most negatively-weighted cycle accounting for depth.

        2. NegativeWeightFinder's version can detect any negative cycle in the given graph (regardless of whether
        or not they include the source). This version is only able to detect negative cycles which start at the source.

        The algorithm when accounting for depth is significantly different at every step that it would necessitate
        almost constant conditionals to check if depth would be accounted for. This is why rather than simply make
        depth a parameter in all of NegativeWeightFinder's methods, there is this separate class.
        :param graph: A graph with 'weight' and 'depth' attributes on all edges.
        """
        super(NegativeWeightDepthFinder, self).__init__(graph)

    def initialize(self, source):
        for node in self.graph:
            self._set_basic_fields(node)

        # The distance from any node to (itself) == 0
        self.distance_to[source] = 0
        self.distance_from[source] = 0

    def relax(self, edge):
        # edge[1] is the head node of the edge, edge[0] is the tail node.
        # because edge[2]['depth'] and self.distance_to[edge[0] are negative logs, we want the max, as the min of
        # e raised to the negative of these will return the max of their values.
        depth = max(self.distance_to[edge[0]], edge[2]['depth'])
        # if the least distance from edge[0] to source (accounting for market depths) + the weight of edge * depth <
        # the least distance to edge[1]
        if edge[2]['weight'] + depth < self.distance_to[edge[1]]:
            self.distance_to[edge[1]] = edge[2]['weight'] + depth
        # todo: there must be a more efficient way to order neighbors by preceding path weights
        # no matter what, adds this edge to the PrioritySet in predecessor_to
        self.predecessor_to[edge[1]].add(edge[0], edge[2]['weight'] + depth)

        # predecessor_from and distance_from are not used in this class as all paths include source. however, should
        # they need to be used in the future, this is the code which allows them to be used in the same manner as
        # distance_to is above.
        # # note we now compare edge[2]['depth'] to distance_from[edge[1]]; it was previously compared to
        # # distance_to[edge[0]], edge[2]['depth']
        # depth = max(self.distance_from[edge[1]], edge[2]['depth'])
        #
        # if edge[2]['weight'] + depth < self.distance_from[edge[0]]:
        #     self.distance_from[edge[0]] = edge[2]['weight'] + depth
        #
        # self.predecessor_from[edge[0]].add(edge[1],
        #                                    self.distance_from[edge[1]] + edge[2]['weight'])

        return True

    def _check_final_condition(self, **kwargs):
        """
        The final condition is if a negative loop exists which contains kwargs['source']. This is checked by seeing if
        self.distance_to[kwargs['source']] < 0. If true, yields that negative cycle.
        :param kwargs:
        :return:
        """
        if 'source' not in kwargs.keys():
            raise ValueError('keyword arguments for _check_final_condition should contain source. This error'
                             'should never show.')

        if self.distance_to[kwargs['source']] < 0:
            yield self._retrace_negative_loop(kwargs['source'],
                                              loop_from_source=False,
                                              ensure_profit=False,
                                              unique_paths=True)


def bellman_ford(graph, source, loop_from_source=False, ensure_profit=False, unique_paths=False, depth=False,
                 starting_amount=1):
    """
    Look at the docstring of the bellman_ford method in the NegativeWeightFinder class. (This is a static wrapper
    function.)

    If depth is true, yields all negatively weighted paths (accounting for depth) when starting with a weight of
    starting_amount.
    """
    return NegativeWeightFinder(graph, depth, starting_amount).bellman_ford(source, loop_from_source, ensure_profit,
                                                                            unique_paths)


def calculate_profit_ratio_for_path(graph, path, depth=False, starting_amount=1):
    ratio = starting_amount
    for i in range(len(path)):
        if i + 1 < len(path):
            start = path[i]
            end = path[i + 1]
            if depth:
                depth = min(ratio, math.exp(-graph[start][end]['depth']))
                ratio = math.exp(-graph[start][end]['weight']) * depth
            else:
                ratio *= math.exp(-graph[start][end]['weight'])

    return ratio / starting_amount
