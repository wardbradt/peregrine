import asyncio
import math

import networkx as nx
from ccxt import async as ccxt


def create_multi_exchange_graph(exchanges: list, digraph=False):
    """
    Returns a MultiGraph representing the markets for each exchange in exchanges. Each edge represents a market.
    Note: does not add edge weights using the ticker's ask and bid prices.
    exchange.load_markets() must have been called for each exchange in exchanges. Will throw a ccxt error if it has not.

    todo: check which error.
    """
    if digraph:
        graph = nx.MultiDiGraph()
    else:
        graph = nx.MultiGraph()

    for exchange in exchanges:
        for market_name in exchange.symbols:
            try:
                base_currency, quote_currency = market_name.split('/')
            # if ccxt returns a market in incorrect format (e.g FX_BTC_JPY on BitFlyer)
            except ValueError:
                continue

            graph.add_edge(base_currency,
                           quote_currency,
                           market_name=market_name,
                           exchange_name=exchange.name.lower())
            if digraph:
                graph.add_edge(quote_currency,
                               base_currency,
                               market_name=market_name,
                               exchange_name=exchange.name.lower())

    return graph


def create_weighted_multi_exchange_digraph(exchanges: list):
    """
    Not optimized
    :param exchanges:
    """
    for i in range(len(exchanges)):
        exchanges[i] = getattr(ccxt, exchanges[i])()

    loop = asyncio.get_event_loop()
    futures = [asyncio.ensure_future(exchange.load_markets()) for exchange in exchanges]
    loop.run_until_complete(asyncio.gather(*futures))

    graph = nx.MultiDiGraph()
    futures = [_add_exchange_to_multi_digraph(graph, exchange, log=True) for exchange in exchanges]
    loop.run_until_complete(asyncio.gather(*futures))


async def _add_exchange_to_multi_digraph(graph: nx.MultiDiGraph, exchange: ccxt.Exchange, log=True):
    tasks = [_add_market_to_multi_digraph(exchange, symbol, graph, log=log) for symbol in exchange.symbols]
    asyncio.wait(tasks)


# todo: refactor. there is a lot of code repetition here with single_exchange.py's _add_market_to_multi_digraph
async def _add_market_to_multi_digraph(exchange: ccxt.Exchange, market_name: str, graph: nx.DiGraph, log=True):
    try:
        ticker = await exchange.fetch_ticker(market_name)
    # any error is solely because of fetch_ticker
    except:
        return

    try:
        ticker_ask = ticker['ask']
        ticker_bid = ticker['bid']
    # ask and bid == None if this market is non existent.
    except TypeError:
        return

    # prevent math error when Bittrex (GEO/BTC) or other API gives 0 as ticker price
    if ticker_ask == 0:
        return
    try:
        base_currency, quote_currency = market_name.split('/')
    # if ccxt returns a market in incorrect format (e.g FX_BTC_JPY on BitFlyer)
    except ValueError:
        return

    if log:
        graph.add_edge(base_currency, quote_currency,
                       market_name=market_name,
                       exchange_name=exchange.id,
                       weight=-math.log(ticker_bid))

        graph.add_edge(quote_currency, base_currency,
                       market_name=market_name,
                       exchange_name=exchange.id,
                       weight=-math.log(1 / ticker_ask))
    else:
        graph.add_edge(base_currency, quote_currency,
                       market_name=market_name,
                       exchange_name=exchange.id,
                       weight=ticker_bid)

        graph.add_edge(quote_currency, base_currency,
                       market_name=market_name,
                       exchange_name=exchange.id,
                       weight=1 / ticker_ask)


async def _add_log_market_to_multi_digraph():
    pass


def multi_graph_to_log_graph(digraph: nx.MultiDiGraph):
    """
    This does not work with the default version of Networkx, but with the fork available at wardbradt/Networkx

    Given weighted MultiDigraph m1, returns a MultiDigraph m2 where for each edge e1 in each edge bunch eb1 of m1, the
    weight w1 of e1 is replaced with log(w1) and the weight w2 of each edge e2 in the opposite edge bunch of eb is
    log(1/w2)

    This function is not optimized.

    todo: allow this function to be used with Networkx DiGraph objects. Should not be that hard, simply return seen
    from self._report in the iterator for digraph's edges() in reportviews.py as it is done for multidigraph's
    edge_bunches()
    """
    result_graph = nx.MultiDiGraph()
    for bunch in digraph.edge_bunches(data=True, seen=True):
        for data_dict in bunch[2]:
            weight = data_dict.pop('weight')
            # if not seen
            if not bunch[3]:
                result_graph.add_edge(bunch[0], bunch[1], -math.log(weight), **data_dict)
            else:
                result_graph.add_edge(bunch[0], bunch[1], -math.log(1/weight), **data_dict)


