import json
import ccxt.async as ccxt
import networkx as nx
from subprocess import check_call
import math
import asyncio


class ExchangeNotInCollectionsError(Exception):
    def __init__(self, market_ticker):
        super(ExchangeNotInCollectionsError, self).__init__("{} is either an invalid exchange or has a broken API."
                                                            .format(market_ticker))


def draw_graph_to_file(graph, dot_name: str, to_file: str):
    nx.drawing.nx_pydot.write_dot(graph, dot_name + '.dot')
    check_call(['dot', '-Tpng', dot_name + '.dot', '-o', to_file])


async def _get_exchange(exchange_name: str):
    exchange = getattr(ccxt, exchange_name)()
    await exchange.load_markets()
    return exchange


def get_exchanges_for_market(market_ticker):
    """
    Returns the list of exchanges on which a market is traded
    """
    with open('collections/collections.json') as f:
        collections = json.load(f)
    for market_name, exchanges in collections.items():
        if market_name == market_ticker:
            return exchanges

    with open('collections/singularly_available_markets.json') as f:
        singularly_available_markets = json.load(f)
    for market_name, exchange in singularly_available_markets:
        if market_name == market_ticker:
            return [exchange]

    raise ExchangeNotInCollectionsError(market_ticker)


def create_exchange_graph(exchange: ccxt.Exchange):
    """
    Returns a simple graph representing exchange. Each edge represents a market.

    exchange.load_markets() must have been called. Will throw a ccxt error if it has not.
    todo: check which error.
    """
    graph = nx.Graph()
    for market_name in exchange.symbols:
        try:
            base_currency, quote_currency = market_name.split('/')
        # if ccxt returns a market in incorrect format (e.g FX_BTC_JPY on BitFlyer)
        except ValueError:
            continue

        graph.add_edge(base_currency, quote_currency, market_name=market_name)

    return graph


def create_multi_exchange_graph(exchanges: list, digraph=False):
    """
    Returns a MultiDigraph representing the markets for each exchange in exchanges. Each edge represents a market.
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


def create_weighted_multi_exchange_digraph(exchanges:list):
    graph = nx.MultiDiGraph()
    loop = asyncio.get_event_loop()
    futures = [_add_exchange_to_multi_graph(graph, exchange) for exchange in exchanges]
    loop.run_until_complete(asyncio.gather(*futures))


async def _add_exchange_to_multi_graph(graph: nx.MultiGraph, exchange: ccxt.Exchange):
    for market_name in exchange.symbols:
        try:
            base_currency, quote_currency = market_name.split('/')
        # if ccxt returns a market in incorrect format (e.g FX_BTC_JPY on BitFlyer)
        except ValueError:
            continue

        ticker = await exchange.fetch_ticker(market_name)

        try:
            ticker_ask = ticker['ask']
            ticker_bid = ticker['bid']
        # ask and bid == None if this market is non existent.
        except TypeError:
            return

        # prevent math error when Bittrex (GEO/BTC) or other API gives 0 as ticker price
        if ticker_ask == 0:
            return

        graph.add_edge(base_currency, quote_currency,
                       market_name=market_name,
                       exchange_name=exchange.id,
                       weight=-math.log(ticker_bid))
        graph.add_edge(quote_currency, base_currency,
                       market_name=market_name,
                       exchange_name=exchange.id,
                       weight=-math.log(1 / ticker_ask))


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


async def load_exchange_graph(exchange_name):
    """
    Returns a DiGraph as described in populate_exchange_graph
    Not optimized.
    """
    exchange = getattr(ccxt, exchange_name)()
    await exchange.load_markets()
    graph = create_exchange_graph(exchange)
    x = await populate_exchange_graph(graph, exchange, log=True)
    return x


async def populate_exchange_graph(graph: nx.Graph, exchange: ccxt.Exchange, log=True):
    """
    Returns a Networkx DiGraph populated with the current ask and bid prices for each market in graph (represented by
    edges)

    Not optimized (because checks if log)
    """
    result = nx.DiGraph()

    tasks = [_add_weighted_edge_to_graph(exchange, edge[2]['market_name'], result, log)
             for edge in graph.edges(data=True)]
    await asyncio.wait(tasks)

    return result


async def _add_weighted_edge_to_graph(exchange: ccxt.Exchange, market_name: str, graph: nx.Graph, log=True):
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
        graph.add_edge(base_currency, quote_currency, weight=-math.log(ticker_bid))
        graph.add_edge(quote_currency, base_currency, weight=-math.log(1 / ticker_ask))
    else:
        graph.add_edge(base_currency, quote_currency, weight=ticker_bid)
        graph.add_edge(quote_currency, base_currency, weight=1 / ticker_ask)
