import asyncio
import math
import networkx as nx
from ccxt import async as ccxt
import warnings


def create_exchange_graph(exchange: ccxt.Exchange):
    """
    Returns a simple graph representing exchange. Each edge represents a market.

    exchange.load_markets() must have been called. Will throw a ccxt error if it has not.
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


async def load_exchange_graph(exchange, name=True, fees=False) -> nx.DiGraph:
    """
    Returns a DiGraph as described in populate_exchange_graph
    """
    if name:
        exchange = getattr(ccxt, exchange)()

    await exchange.load_markets()

    fee = 0
    if fees:
        if 'maker' in exchange.fees['trading']:
            fee = exchange.fees['trading']['maker']
        else:
            warnings.warn("The fees for {} have not yet been implemented into the library. Values will be calculated"
                          "estimating a .2% maker fee.".format(exchange))
            fee = 0.002

    # print("a: " + str(exchange.fees))

    graph = nx.DiGraph()

    tasks = [_add_weighted_edge_to_graph(exchange, market_name, graph, log=True, fee=fee)
             for market_name in exchange.symbols]
    await asyncio.wait(tasks)

    return graph


async def populate_exchange_graph(graph: nx.Graph, exchange: ccxt.Exchange, log=True) -> nx.DiGraph:
    """
    Returns a Networkx DiGraph populated with the current ask and bid prices for each market in graph (represented by
    edges)
    """
    result = nx.DiGraph()

    tasks = [_add_weighted_edge_to_graph(exchange, edge[2]['market_name'], result, log)
             for edge in graph.edges(data=True)]
    await asyncio.wait(tasks)

    return result


async def _add_weighted_edge_to_graph(exchange: ccxt.Exchange, market_name: str, graph: nx.DiGraph, log=True, fee=0):
    try:
        ticker = await exchange.fetch_ticker(market_name)
    # any error is solely because of fetch_ticker
    except:
        warnings.warn("Market {} is unavailable at this time.".format(market_name))
        return

    fee_scalar = 1 - fee

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
        graph.add_edge(base_currency, quote_currency, weight=-math.log(fee_scalar * ticker_bid))
        graph.add_edge(quote_currency, base_currency, weight=-math.log(fee_scalar * 1 / ticker_ask))
    else:
        graph.add_edge(base_currency, quote_currency, weight=fee_scalar * ticker_bid)
        graph.add_edge(quote_currency, base_currency, weight=fee_scalar * 1 / ticker_ask)
