import asyncio
import math

import networkx as nx
from ccxt import async as ccxt


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


async def load_exchange_graph(exchange_name) -> nx.DiGraph:
    """
    Returns a DiGraph as described in populate_exchange_graph
    """
    exchange = getattr(ccxt, exchange_name)()
    await exchange.load_markets()

    graph = nx.DiGraph()

    tasks = [_add_weighted_edge_to_graph(exchange, market_name, graph, log=True)
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


async def _add_weighted_edge_to_graph(exchange: ccxt.Exchange, market_name: str, graph: nx.DiGraph, log=True):
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
