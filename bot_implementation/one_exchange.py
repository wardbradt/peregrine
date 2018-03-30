import asyncio
from peregrinearb import load_exchange_graph, bellman_ford
import math


def trade_from_source(exchange, source, amount):
    """
    Should not be used in its current form due to the following:
    1. It is possible that the trades upon which the algorithm detected an arbitrage opportunity have been executed
    (and thus the opportunity may or may not still exist)
    2. The Bellman Ford implementation does not (currently) account for the amounts specified in each order. This is the
    biggest issue.
    3. It is not maximally profitable as it iterates through each negative cycle (arbitrage opportunity) only once.

    This is a bare-bones proof-of-concept: it shows how the algorithm could be used for financial gain.

    todo: implement an asynchronous version for exchanges which allow margin trading.

    :param exchange: A ccxt Exchange object. Should be "pre-loaded" with all necessary data (such as the API key).
    :param source: The ticker for any currency in exchange.
    :param amount: Starting amount of source that will be traded.
    """
    loop = asyncio.get_event_loop()
    graph = loop.run_until_complete(load_exchange_graph(exchange, name=False, fees=True))

    paths = bellman_ford(graph, source, loop_from_source=True, unique_paths=True)
    for path in paths:
        for i in range(len(path) - 1):
            loop.run_until_complete(exchange.create_order(
                path[i] + '/' + path[i + 1],
                'limit',
                'sell',
                amount,
                math.exp(-graph[path[i]][path[i + 1]]['weight'])),
                )
            amount *= math.exp(-graph[path[i]][path[i + 1]]['weight'])
