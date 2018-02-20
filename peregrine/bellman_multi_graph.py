import math
import networkx as nx
import asyncio


def _get_greatest_edge_in_bunch(edge_bunch, weight='weight'):
    """
    Edge bunch must be of the format (u, v, d) where u and v are the tail and head nodes (respectively) and d is a list
    of dicts holding the edge_data for each edge in the bunch
    
    Not optimized because currently the only place that calls it first checks len(edge_bunch[2]) > 0
    todo: could take only edge_bunch[2] as parameter
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
        self.predecessor = {}
        self.distance_to = {}

    def initialize(self, source):
        for node in self.graph:
            # Initialize all distance_to values to infinity and all predecessor values to None
            self.distance_to[node] = float('Inf')
            self.predecessor[node] = None
        # The distance from any node to (itself) == 0
        self.distance_to[source] = 0

    def first_iteration(self):
        futures = [asyncio.ensure_future(self._process_edge_bunch(edge_bunch))
                   for edge_bunch in self.graph.edge_bunches(data=True)]
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*futures))

    async def _process_edge_bunch(self, edge_bunch):
        """
        Todo: refactor for general usage (mainly have to change the first if statements)
        """
        # this assumes that market symbols are uniform across all exchanges (i.e every market A/B on on exchange is
        # always represented as A/B, never B/A.
        # if edge_bunch[0] == base currency, the edge weights represent the bid price so we look for
        # the greatest edge weight
        if edge_bunch[0] == edge_bunch[2][0]['market_name'].split('/')[0]:
            ideal_edge = _get_greatest_edge_in_bunch(edge_bunch)
        # else, edge_bunch[1] == quote currency so we look for the least edge weight.
        else:
            ideal_edge = _get_least_edge_in_bunch(edge_bunch)

        # todo: does this ever happen?
        if ideal_edge['weight'] == -float('Inf'):
            return

        # todo: there is probably a more efficient way to keep only the edges which show minimum ask and maximum bid
        self.new_graph.add_edge(edge_bunch[0], edge_bunch[1],
                                exchange_name=ideal_edge['exchange_name'],
                                market_name=ideal_edge['market_name'],
                                weight=ideal_edge['weight'])

        # todo: delete print statements. they test if this condition is always true.
        if self.distance_to[edge_bunch[0]] + ideal_edge['weight'] <= self.distance_to[edge_bunch[1]]:
            self.distance_to[edge_bunch[1]] = self.distance_to[edge_bunch[0]] + ideal_edge['weight']
            self.predecessor[edge_bunch[1]] = edge_bunch[0]

    def bellman_ford(self, source):
        """
        :param source: The node in graph from which the values in distance_to will be calculated.
        """
        self.initialize(source)

        # on first iteration, load market prices.
        self.first_iteration()

        # After len(graph) - 1 passes, algorithm is complete.
        for i in range(1, len(self.new_graph) - 1):
            # for each node in the graph, test if the distance to each of its siblings is shorter by going from
            # source->base_currency + base_currency->quote_currency
            for edge in self.new_graph.edges(data=True):
                if self.distance_to[edge[0]] + edge[2]['weight'] < self.distance_to[edge[1]]:
                    self.distance_to[edge[1]] = self.distance_to[edge[0]] + edge[2]['weight']
                    self.predecessor[edge[1]] = edge[0]

        for edge in self.new_graph.edges(data=True):
            if self.distance_to[edge[0]] + edge[2]['weight'] < self.distance_to[edge[1]]:
                return retrace_negative_loop(self.predecessor, source)

        return None


def retrace_negative_loop(predecessor, start):
    """
    Does not currently work as a node may be encountered more than once.
    :param predecessor:
    :param start:
    :return:
    """
    arbitrage_loop = [start]
    next_node = start
    while True:
        next_node = predecessor[next_node]
        if next_node not in arbitrage_loop:
            arbitrage_loop.insert(0, next_node)
        else:
            arbitrage_loop.insert(0, next_node)
            arbitrage_loop = arbitrage_loop[arbitrage_loop.index(next_node):]
            return arbitrage_loop


def bellman_ford(graph: nx.MultiGraph, source):
    return NegativeWeightFinderMulti(graph).bellman_ford(source)


def calculate_profit_ratio_for_path(graph, path):
    money = 1
    for i in range(len(path)):
        if i + 1 < len(path):
            start = path[i]
            end = path[i + 1]
            # todo: rate should not have to be inversed
            rate = math.exp(-graph[start][end]['weight'])
            money *= rate
    return money


def print_profit_opportunity_for_path(graph, path):
    money = 100
    print("Starting with %(money)i in %(currency)s" % {"money": money, "currency": path[0]})

    for i in range(len(path)):
        if i + 1 < len(path):
            start = path[i]
            end = path[i + 1]
            x = graph[start]
            y = x[end][0]
            # todo: we should not have to add [0] to this. it should simply be [start][end][0]['weight'].
            rate = math.exp(-graph[start][end][0]['weight'])
            money *= rate
            print("{} to {} at {} = {} on {} for {}".format(start, end, rate, money,
                                                            graph[start][end][0]['exchange_name'],
                                                            graph[start][end][0]['market_name']))
