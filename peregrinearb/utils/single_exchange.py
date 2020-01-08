import asyncio
import math
import networkx as nx
import ccxt.async_support as ccxt
import datetime
import logging
from .logging_utils import FormatForLogAdapter

__all__ = [
    'FeesNotAvailable',
    'create_exchange_graph',
    'load_exchange_graph',
]

adapter = FormatForLogAdapter(logging.getLogger('peregrinearb.utils.single_exchange'))


class FeesNotAvailable(Exception):
    pass


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


async def load_exchange_graph(exchange, name=True, fees=True, suppress=None, depth=False, tickers=None) -> nx.DiGraph:
    """
    Returns a networkx DiGraph populated with the current ask and bid prices for each market in graph (represented by
    edges). If depth, also adds an attribute 'depth' to each edge which represents the current volume of orders
    available at the price represented by the 'weight' attribute of each edge.
    """
    if suppress is None:
        suppress = ['markets']

    if name:
        exchange = getattr(ccxt, exchange)()

    if tickers is None:
        adapter.info('Fetching tickers')
        tickers = await exchange.fetch_tickers()
        adapter.info('Fetched tickers')

    market_count = len(tickers)
    adapter.info('Loading exchange graph', marketCount=market_count)

    adapter.debug('Initializing empty graph with exchange_name and timestamp attributes')
    graph = nx.DiGraph()

    # todo: get exchange's server time?
    graph.graph['exchange_name'] = exchange.id
    graph.graph['datetime'] = datetime.datetime.now(tz=datetime.timezone.utc)
    adapter.debug('Initialized empty graph with exchange_name and timestamp attributes')

    async def add_edges():
        tasks = [_add_weighted_edge_to_graph(exchange, market_name, graph, log=True, fees=fees,
                                             suppress=suppress, ticker=ticker, depth=depth, )
                 for market_name, ticker in tickers.items()]
        await asyncio.wait(tasks)

    if fees:
        for i in range(20):
            try:
                adapter.info('Loading fees', iteration=i)
                # must load markets to get fees
                await exchange.load_markets()
            except (ccxt.DDoSProtection, ccxt.RequestTimeout) as e:
                if i == 19:
                    adapter.warning('Rate limited on final iteration, raising error', iteration=i)
                    raise e
                adapter.warning('Rate limited when loading markets', iteration=i)
                await asyncio.sleep(0.1)
            except ccxt.ExchangeNotAvailable as e:
                if i == 19:
                    adapter.warning('Cannot load markets due to ExchangeNotAvailable error, '
                                    'graph will not be loaded.', iteration=i)
                    raise e
                adapter.warning('Received ExchangeNotAvailable error when loading markets', iteration=i)
            else:
                break

        adapter.info('Loaded fees', iteration=i, marketCount=market_count)

        currency_count = len(exchange.currencies)
        adapter.info('Adding data to graph', marketCount=market_count, currencyCount=currency_count)
        await add_edges()
        adapter.info('Added data to graph', marketCount=market_count, currencyCount=currency_count)
    else:
        adapter.info('Adding data to graph', marketCount=market_count)
        await add_edges()
        adapter.info('Added data to graph', marketCount=market_count)

    adapter.debug('Closing connection')
    await exchange.close()
    adapter.debug('Closed connection')

    adapter.info('Loaded exchange graph')
    return graph


async def _add_weighted_edge_to_graph(exchange: ccxt.Exchange, market_name: str, graph: nx.DiGraph, log=True,
                                      fees=False, suppress=None, ticker=None, depth=False, ):
    """
    todo: add global variable to bid_volume/ ask_volume to see if all tickers (for a given exchange) have value == None
    Returns a Networkx DiGraph populated with the current ask and bid prices for each market in graph (represented by
    edges).
    :param exchange: A ccxt Exchange object
    :param market_name: A string representing a cryptocurrency market formatted like so:
    '{base_currency}/{quote_currency}'
    :param graph: A Networkx DiGraph upon
    :param log: If the edge weights given to the graph should be the negative logarithm of the ask and bid prices. This
    is necessary to calculate arbitrage opportunities.
    :param fees: If fees should be taken into account for prices.
    :param suppress: A list or set which tells which types of warnings to not throw. Accepted elements are 'markets'.
    :param ticker: A dictionary representing a market as returned by ccxt's Exchange's fetch_ticker method
    :param depth: If True, also adds an attribute 'depth' to each edge which represents the current volume of orders
    available at the price represented by the 'weight' attribute of each edge.
    """
    adapter.debug('Adding edge to graph', market=market_name)
    if ticker is None:
        try:
            adapter.info('Fetching ticker', market=market_name)
            ticker = await exchange.fetch_ticker(market_name)
            adapter.info('Fetched ticker', market=market_name)
        # any error is solely because of fetch_ticker
        except:
            if 'markets' not in suppress:
                adapter.warning('Market is unavailable at this time. It will not be included in the graph.',
                                market=market_name)
            return

    if fees:
        if 'taker' in exchange.markets[market_name]:
            # we always take the taker side because arbitrage depends on filling orders
            # sell_fee_dict = exchange.calculate_fee(market_name, 'limit', 'sell', 0, 0, 'taker')
            # buy_fee_dict = exchange.calculate_fee(market_name, 'limit', 'buy', 0, 0, 'taker')
            fee = exchange.markets[market_name]['taker']
        else:
            if 'fees' not in suppress:
                adapter.warning("The fees for {} have not yet been implemented into ccxt's uniform API."
                                .format(exchange))
                raise FeesNotAvailable('Fees are not available for {} on {}'.format(market_name, exchange.id))
            else:
                fee = 0.002
    else:
        fee = 0

    fee_scalar = 1 - fee

    try:
        bid_rate = ticker['bid']
        ask_rate = ticker['ask']
        if depth:
            bid_volume = ticker['bidVolume']
            ask_volume = ticker['askVolume']
            if bid_volume is None:
                adapter.warning('Market is unavailable because its bid volume was given as None. '
                                'It will not be included in the graph.', market=market_name)
                return
            if ask_volume is None:
                adapter.warning('Market is unavailable because its ask volume was given as None. '
                                'It will not be included in the graph.', market=market_name)
                return
    # ask and bid == None if this market is non existent.
    except TypeError:
        adapter.warning('Market is unavailable at this time. It will not be included in the graph.',
                        market=market_name)
        return

    # Exchanges give asks and bids as either 0 or None when they do not exist.
    # todo: should we account for exchanges upon which an ask exists but a bid does not (and vice versa)? Would this
    # cause bugs?
    if ask_rate == 0 or bid_rate == 0 or ask_rate is None or bid_rate is None:
        adapter.warning('Market is unavailable at this time. It will not be included in the graph.',
                        market=market_name)
        return
    try:
        base_currency, quote_currency = market_name.split('/')
    # if ccxt returns a market in incorrect format (e.g FX_BTC_JPY on BitFlyer)
    except ValueError:
        if 'markets' not in suppress:
            adapter.warning('Market is unavailable at this time due to incorrect formatting. '
                            'It will not be included in the graph.', market=market_name)
        return

    if log:
        if depth:
            graph.add_edge(base_currency, quote_currency, weight=-math.log(fee_scalar * bid_rate),
                           depth=-math.log(bid_volume), market_name=market_name, trade_type='SELL',
                           fee=fee, volume=bid_volume, no_fee_rate=bid_rate)
            graph.add_edge(quote_currency, base_currency, weight=-math.log(fee_scalar * 1 / ask_rate),
                           depth=-math.log(ask_volume * ask_rate), market_name=market_name, trade_type='BUY',
                           fee=fee, volume=ask_volume, no_fee_rate=ask_rate)
        else:
            graph.add_edge(base_currency, quote_currency, weight=-math.log(fee_scalar * bid_rate),
                           market_name=market_name, trade_type='SELL', fee=fee, no_fee_rate=bid_rate)
            graph.add_edge(quote_currency, base_currency, weight=-math.log(fee_scalar * 1 / ask_rate),
                           market_name=market_name, trade_type='BUY', fee=fee, no_fee_rate=ask_rate)
    else:
        if depth:
            graph.add_edge(base_currency, quote_currency, weight=fee_scalar * bid_rate, depth=bid_volume,
                           market_name=market_name, trade_type='SELL', fee=fee, volume=bid_volume, no_fee_rate=bid_rate)
            graph.add_edge(quote_currency, base_currency, weight=fee_scalar * 1 / ask_rate, depth=ask_volume,
                           market_name=market_name, trade_type='BUY', fee=fee, volume=ask_volume, no_fee_rate=ask_rate)
        else:
            graph.add_edge(base_currency, quote_currency, weight=fee_scalar * bid_rate,
                           market_name=market_name, trade_type='SELL', fee=fee, no_fee_rate=bid_rate)
            graph.add_edge(quote_currency, base_currency, weight=fee_scalar * 1 / ask_rate,
                           market_name=market_name, trade_type='BUY', fee=fee, no_fee_rate=ask_rate)

    adapter.debug('Added edge to graph', market=market_name)
