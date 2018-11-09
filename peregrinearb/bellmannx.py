import math
import networkx as nx
from .utils import last_index_in_list, FormatForLogAdapter
import asyncio
from .utils import load_exchange_graph
import logging
__all__ = [
    'NegativeWeightFinder',
    'NegativeWeightDepthFinder',
    'bellman_ford',
    'find_opportunities_on_exchange',
    'calculate_profit_ratio_for_path',
    'SeenNodeError',
    'get_starting_volume',
]


class SeenNodeError(Exception):
    pass


adapter = FormatForLogAdapter(logging.getLogger('peregrinearb.bellmannx'))


class NegativeWeightFinder:
    __slots__ = ['graph', 'predecessor_to', 'distance_to', 'seen_nodes']

    def __init__(self, graph: nx.Graph):
        self.graph = graph
        self.predecessor_to = {}
        # the maximum weight which can be transferred from source to each node
        self.distance_to = {}

        self.seen_nodes = set()

    def reset_all_but_graph(self):
        self.predecessor_to = {}
        self.distance_to = {}

        self.seen_nodes = set()

    def _set_basic_fields(self, node):
        # todo: change predecessor_to to a dict and get rid of loop_from_source
        # Initialize all distance_to values to infinity and all predecessor_to values to None
        self.distance_to[node] = float('Inf')
        self.predecessor_to[node] = None

    def initialize(self, source):
        for node in self.graph:
            self._set_basic_fields(node)

        # The distance from any node to (itself) == 0
        self.distance_to[source] = 0

    def bellman_ford(self, source, unique_paths=True):
        """
        :param unique_paths: If true, ensures that no duplicate paths are returned.
        """
        if source not in self.graph:
            raise ValueError('source {} not in graph'.format(source))

        adapter.debug('Running bellman_ford')
        self.initialize(source)

        adapter.debug('Relaxing edges')
        # After len(graph) - 1 passes, algorithm is complete.
        for i in range(len(self.graph) - 1):
            # for each node in the graph, test if the distance to each of its siblings is shorter by going from
            # source->base_currency + base_currency->quote_currency
            for edge in self.graph.edges(data=True):
                self.relax(edge)
        adapter.debug('Finished relaxing edges')

        paths = self._check_final_condition(unique_paths=unique_paths)

        adapter.debug('Ran bellman_ford')
        return paths

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
        adapter.debug('Checking final condition')
        for edge in self.graph.edges(data=True):
            if self.distance_to[edge[0]] + edge[2]['weight'] < self.distance_to[edge[1]]:
                try:
                    path = self._retrace_negative_loop(edge[1], unique_paths=kwargs['unique_paths'])
                except SeenNodeError:
                    adapter.debug('SeenNodeError raised')
                    continue

                adapter.debug('Yielding path', path=str(path))
                yield path

    def relax(self, edge):
        adapter.debug('Relaxing edge', fromnode=edge[1], tonode=edge[0])
        if self.distance_to[edge[0]] + edge[2]['weight'] < self.distance_to[edge[1]]:
            self.distance_to[edge[1]] = self.distance_to[edge[0]] + edge[2]['weight']
            self.predecessor_to[edge[1]] = edge[0]

        return True

    def _retrace_negative_loop(self, start, unique_paths=False):
        """
        :return: negative loop path
        """
        adapter.debug('Retracing loops')
        if unique_paths and start in self.seen_nodes:
            raise SeenNodeError

        arbitrage_loop = [start]
        next_node = start
        while True:
            next_node = self.predecessor_to[next_node]
            # if negative cycle is complete
            if next_node in arbitrage_loop:
                arbitrage_loop = arbitrage_loop[:last_index_in_list(arbitrage_loop, next_node) + 1]
                arbitrage_loop.insert(0, next_node)
                return arbitrage_loop

            # if next_node in arbitrage_loop, next_node in self.seen_nodes. thus, this conditional must proceed
            # checking if next_node in arbitrage_loop
            if unique_paths and next_node in self.seen_nodes:
                raise SeenNodeError(next_node)

            arbitrage_loop.insert(0, next_node)
            self.seen_nodes.add(next_node)


class NegativeWeightDepthFinder(NegativeWeightFinder):

    def _retrace_negative_loop(self, start, unique_paths=False):
        """
        Unlike NegativeWeightFinder's _retrace_negative_loop, this returns a dict structured as
        {'loop': arbitrage_loop, 'minimum' : minimum}, where arbitrage_loop is a negatively-weighted cycle and minimum
        is the least weight that can be started with at source.
        """
        if unique_paths and start in self.seen_nodes:
            raise SeenNodeError

        adapter.debug('Retracing loops')

        arbitrage_loop = [start]
        prior_node = self.predecessor_to[arbitrage_loop[0]]
        # the minimum weight which can be transferred without being limited by edge depths
        minimum = self.graph[prior_node][arbitrage_loop[0]]['depth']
        arbitrage_loop.insert(0, prior_node)
        while True:
            if arbitrage_loop[0] in self.seen_nodes and unique_paths:
                raise SeenNodeError
            self.seen_nodes.add(prior_node)

            prior_node = self.predecessor_to[arbitrage_loop[0]]
            edge_weight = self.graph[prior_node][arbitrage_loop[0]]['weight']
            edge_depth = self.graph[prior_node][arbitrage_loop[0]]['depth']
            # if minimum is the limiting volume
            if edge_weight + edge_depth < minimum:
                minimum = max(minimum - edge_weight, edge_depth)
            # if edge_depth is the limiting volume
            elif edge_weight + edge_depth > minimum:
                minimum = edge_depth

            if prior_node in arbitrage_loop:
                arbitrage_loop = arbitrage_loop[:last_index_in_list(arbitrage_loop, prior_node) + 1]
                arbitrage_loop.insert(0, prior_node)
                adapter.info('Retraced loop')
                return {'loop': arbitrage_loop, 'minimum': minimum}

            arbitrage_loop.insert(0, prior_node)


def bellman_ford(graph, source, unique_paths=False):
    """
    Look at the docstring of the bellman_ford method in the NegativeWeightFinder class. (This is a static wrapper
    function.)

    If depth is true, yields all negatively weighted paths (accounting for depth) when starting with a weight of
    starting_amount.
    """
    return NegativeWeightFinder(graph).bellman_ford(source, unique_paths)


def find_opportunities_on_exchange(exchange_name, source, unique_paths=False, depth=False):
    """
    A high level function to find intraexchange arbitrage opportunities on a specified exchange.
    """
    graph = asyncio.get_event_loop().run_until_complete(load_exchange_graph(exchange_name, depth=depth))
    if depth:
        finder = NegativeWeightDepthFinder(graph)
        return finder.bellman_ford(source, unique_paths)

    return bellman_ford(graph, source, unique_paths)


def get_starting_volume(graph, path):
    adapter.info('Gathering path data', path=str(path))

    volume_scalar = 1
    start = path[0]
    end = path[1]
    initial_volume = math.exp(-graph[start][end]['depth'])
    previous_volume = initial_volume * math.exp(-graph[start][end]['weight'])
    for i in range(1, len(path) - 1):
        start = path[i]
        end = path[i + 1]
        current_max_volume = math.exp(-graph[start][end]['depth'])
        if previous_volume > current_max_volume:
            volume_scalar *= current_max_volume / previous_volume
        previous_volume *= math.exp(-graph[start][end]['weight'])
    return initial_volume * volume_scalar


def calculate_profit_ratio_for_path(graph, path, depth=False, starting_amount=1, gather_path_data=False):
    """
    If gather_path_data, returns a two-tuple where the first element is the profit ratio for the given path and the
    second element is a dict keyed by market symbol and valued by a a dict with 'rate' and 'volume' keys, corresponding
    to the rate and maximum volume for the trade.
    The volume and rate are always in terms of base currency.
    """
    adapter.info('Calculating profit ratio')
    if gather_path_data:
        path_data = []

    ratio = starting_amount
    for i in range(len(path) - 1):
        start = path[i]
        end = path[i + 1]
        if depth:
            # volume and rate_with_fee are in terms of start, may be base or quote currency.
            rate_with_fee = math.exp(-graph[start][end]['weight'])
            volume = min(ratio, math.exp(-graph[start][end]['depth']))
            ratio = volume * rate_with_fee

            if gather_path_data:
                sell = graph[start][end]['trade_type'] == 'SELL'
                # for buy orders, put volume in terms of base currency.
                if not sell:
                    volume /= graph[start][end]['no_fee_rate']

                path_data.append({'market_name': graph[start][end]['market_name'],
                                  'rate': graph[start][end]['no_fee_rate'],
                                  'fee': graph[start][end]['fee'],
                                  'volume': volume,
                                  # todo: change order and its usages to type
                                  # if start comes before end in path, this is a sell order.
                                  'order': 'SELL' if sell else 'BUY'})
        else:
            ratio *= math.exp(-graph[start][end]['weight'])

    adapter.info('Calculated profit ratio')

    if gather_path_data:
        return (ratio / starting_amount), path_data
    return ratio / starting_amount
