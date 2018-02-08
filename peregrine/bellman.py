import math
import ccxt.async as ccxt
import asyncio


def initialize_completed_graph_for_exchange(exchange_name):
    graph = {}
    exchange = getattr(ccxt, exchange_name)()
    exchange.load_markets()
    for market_name, market_info in exchange.markets.items():
        # todo: is there a benefit from differing bid and ask?
        # for now, treating price as average of ask and bid
        ticker_exchange_rate = (exchange.fetch_ticker(market_name)['ask'] + exchange.fetch_ticker(market_name)[
            'bid']) / 2
        # prevent math error when Bittrex (GEO/BTC) or other API gives 0 as ticker price
        if ticker_exchange_rate == 0:
            continue

        conversion_rate = -math.log(ticker_exchange_rate)
        base_currency, quote_currency = market_name.split('/')

        if base_currency not in graph:
            graph[base_currency] = {}
        if quote_currency not in graph:
            graph[quote_currency] = {}

        graph[base_currency][quote_currency] = conversion_rate
        graph[quote_currency][base_currency] = -conversion_rate

    return graph


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
            if distance_to[quote_currency] < distance_to[base_currency_node] + graph[base_currency_node][
                quote_currency]:
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
