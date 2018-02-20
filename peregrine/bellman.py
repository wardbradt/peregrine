import math
import ccxt.async as ccxt
import asyncio


#############################################################
# This file is deprecated in favor of bellmannx.py. However,
# because the script in this file is more low level and some
# prefer it, it remains in the repository. Feel free to
# contribute to it as you wish.
#############################################################


class AsyncBellmanGraphInitializer:

    def __init__(self, exchange: ccxt.Exchange):
        self.graph = {}
        self.exchange = exchange

    def initialize_completed_graph_for_exchange(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(asyncio.ensure_future(self.exchange.load_markets())))
        futures = [asyncio.ensure_future(self._process_market(market_name)) for market_name in
                   self.exchange.markets.keys()]
        loop.run_until_complete(asyncio.gather(*futures))

        return self.graph

    async def _process_market(self, market: str):
        try:
            ticker = await self.exchange.fetch_ticker(market)
        except ccxt.BaseError:
            return
        # any error is solely because of fetch_ticker
        except Exception:
            return
        try:
            # todo: make bid and ask represent the different weights of the two parallel directed edges representing
            # each market
            # for now, treating price as average of ask and bid
            # can sell for bid, can buy for ask.
            ticker_exchange_rate = (ticker['ask'] + ticker['bid']) / 2
        # ask and bid == None if this market is non existent.
        except TypeError:
            return

        # prevent math error when Bittrex (GEO/BTC) or other API gives 0 as ticker price
        if ticker_exchange_rate == 0:
            return

        try:
            base_currency, quote_currency = market.split('/')
        # if ccxt returns a market in incorrect format (e.g FX_BTC_JPY on BitFlyer)
        except ValueError:
            return

        if base_currency not in self.graph:
            self.graph[base_currency] = {}
        if quote_currency not in self.graph:
            self.graph[quote_currency] = {}

        conversion_rate = -math.log(ticker_exchange_rate)
        self.graph[base_currency][quote_currency] = conversion_rate
        self.graph[quote_currency][base_currency] = -conversion_rate


def initialize_completed_graph_for_exchange(exchange_name):
    return AsyncBellmanGraphInitializer(getattr(ccxt, exchange_name)()).initialize_completed_graph_for_exchange()


# Step 1: For each node prepare the distance_to and predecessor
def initialize(graph, source):
    # represents the shortest distance from source to n where n is one of all nodes in graph
    distance_to = {}
    # for each key k in predecessor, its value is the node which allows for the shortest path to k
    predecessor = {}
    for base_currency in graph:
        # Initialize all distance_to values to infinity and all predecessor values to None
        distance_to[base_currency] = float('Inf')
        predecessor[base_currency] = None
    # The distance from any node to (itself) == 0
    distance_to[source] = 0
    return distance_to, predecessor


def relax(base_currency, quote_currency, graph, distance_to, predecessor):
    """
    :param base_currency: the node (dict) representing the base currency in graph
    :param quote_currency: the node (dict) representing the quote currency in graph
    """
    # If the currently saved distance to quote_currency > source->base_currency + base_currency->quote_currency
    try:
        if distance_to[quote_currency] > distance_to[base_currency] + graph[base_currency][quote_currency]:
            distance_to[quote_currency] = distance_to[base_currency] + graph[base_currency][quote_currency]
            # the head of the edge preceding quote_currency on the fastest route to quote_currency is base_currency
            predecessor[quote_currency] = base_currency
    # distance_to[base_currency] will never throw an error because base_currency is a node in the graph and
    # initialize has ensured that all graph nodes are in distance_to. The code in this except block is treating
    # distance_to[quote_currency] as float('Inf'). The if statement in the try block would be true, so it executes the
    # code in the if block.
    # if an error was thrown on distance_to[quote_currency]
    except KeyError:
        distance_to[quote_currency] = distance_to[base_currency] + graph[base_currency][quote_currency]
        predecessor[quote_currency] = base_currency


def bellman_ford(graph, source):
    """
    todo: write the intended format for graph
    :param graph:
    :param source: The node in graph from which the values in distance_to will be calculated.
    :return: two dicts, the first of which is distance_to, which stores the shortest distance from source to each node
    in the graph. Each value in distance_to is initialized to float('Inf'). The second dict is predecessor, which, for
    each node in graph, stores the node immediately preceding it on the shortest path to it.
    """
    distance_to, predecessor = initialize(graph, source)
    # After len(graph) - 1 passes, algorithm is complete.
    for i in range(len(graph) - 1):
        # for each node in the graph, test if the distance to each of its siblings is shorter by going from
        # source->base_currency + base_currency->quote_currency
        for base_currency_node in graph.keys():
            # For each neighbour of base_currency_node
            for quote_currency in graph[base_currency_node]:
                relax(base_currency_node, quote_currency, graph, distance_to, predecessor)

    # Step 3: check for negative-weight cycles
    for base_currency_node in graph:
        for quote_currency in graph[base_currency_node]:
            if distance_to[quote_currency] < distance_to[base_currency_node] + \
                    graph[base_currency_node][quote_currency]:
                return retrace_negative_loop(predecessor, source)
    return None


def retrace_negative_loop(predecessor, start):
    arbitrage_loop = [start]
    next_node = start
    while True:
        next_node = predecessor[next_node]
        if next_node not in arbitrage_loop:
            arbitrage_loop.append(next_node)
        else:
            arbitrage_loop.append(next_node)
            arbitrage_loop = arbitrage_loop[arbitrage_loop.index(next_node):]
            return arbitrage_loop


def calculate_profit_ratio_for_path(graph, path):
    money = 1
    for i in range(len(path)):
        if i + 1 < len(path):
            start = path[i]
            end = path[i + 1]
            # todo: rate should not have to be inversed
            rate = 1 / math.exp(-graph[start][end])
            money *= rate
    return money


def print_profit_opportunity_for_path(graph, path):
    money = 100
    print("Starting with %(money)i in %(currency)s" % {"money": money, "currency": path[0]})

    for i in range(len(path)):
        if i + 1 < len(path):
            start = path[i]
            end = path[i + 1]
            # todo: rate should not have to be inversed
            rate = 1 / math.exp(-graph[start][end])
            money *= rate
            print("%(start)s to %(end)s at %(rate)f = %(money)f" % {"start": start, "end": end, "rate": rate,
                                                                    "money": money})


def get_all_paths_for_exchange(exchange_name):
    graph = initialize_completed_graph_for_exchange(exchange_name)
    return get_all_paths_for_graph(graph)


def get_path_from_node(graph: dict, source: str):
    return bellman_ford(graph, source)


def get_all_paths_for_graph(graph: dict):
    paths = []
    for source_node in graph.keys():
        paths.append(bellman_ford(graph, source_node))
    return paths


def bellman_all_exchanges_example():
    paths = {}
    exchanges = [exchange for exchange in ccxt.exchanges if 'US' in getattr(ccxt, exchange)().countries]
    for exchange_name in exchanges:
        try:
            initializer = AsyncBellmanGraphInitializer(getattr(ccxt, exchange_name)())
            graph = initializer.initialize_completed_graph_for_exchange()
        except ccxt.BaseError:
            continue

        if len(graph.keys()) > 0:
            path = get_path_from_node(graph, list(graph.keys())[0])
        else:
            continue
        if path is None:
            print(exchange_name + " has no negative weight cycles")
            continue
        paths[exchange_name] = {'profit_ratio': calculate_profit_ratio_for_path(graph, path), 'path': str(path)}
        print(exchange_name + " " + str(paths[exchange_name]))
    print(paths)
