from unittest import TestCase
from peregrinearb import format_graph_for_json, load_exchange_graph
import networkx as nx
import ccxt.async_support as ccxt
import asyncio
import math


class TestExchange(ccxt.Exchange):

    def __init__(self, config={}, balances=None, name=None, tickers=None, symbols=None, markets=None, currencies=None,
                 wait_time=0, wait_time_limit=0):
        super(TestExchange, self).__init__()
        if balances is None:
            balances = {'free': {}}
        if tickers is None:
            tickers = {}
        if symbols is None:
            symbols = [key for key in tickers.keys()]
        if markets is None:
            markets = {}
        if currencies is None:
            currencies = []

        self.currencies = currencies
        self.markets = markets
        self.symbols = symbols
        self.currencies = currencies
        self.balances = balances
        self.id = name
        self.orders = {}
        self.wait_time = wait_time

        # How many times fetch_order should be called before returning {'status': 'closed'}
        self.wait_time_limit = wait_time_limit
        self._wait_time_increment = 0

    async def fetch_tickers(self, symbols=None, params={}):
        return self.tickers

    async def fetch_ticker(self, symbol, params={}):
        return self.tickers[symbol]

    async def load_markets(self, reload=False):
        return self.markets

    async def fetch_balance(self):
        return self.balances

    async def create_limit_buy_order(self, symbol, *args):
        base, quote = symbol.split('/')
        volume = min(self.balances['free'][quote], args[0] * args[1])

        self.balances['free'][quote] -= volume * args[1]
        if base in self.balances['free']:
            self.balances['free'][base] += volume
        else:
            self.balances['free'][base] = volume

        return {'id': 0}

    async def create_limit_sell_order(self, symbol, *args):
        base, quote = symbol.split('/')
        volume = min(args[0], self.balances['free'][base])

        self.balances['free'][base] -= volume
        if quote in self.balances['free']:
            self.balances['free'][quote] += volume * args[1]
        else:
            self.balances['free'][quote] = volume * args[1]

        return {'id': 0}

    async def fetch_order(self, id, symbol=None, params={}):
        await asyncio.sleep(self.wait_time)
        if self._wait_time_increment >= self.wait_time_limit:
            self._wait_time_increment = 0
            return {'status': 'closed'}

        self._wait_time_increment += 1
        return {'status': 'open'}

    async def cancel_order(self, id, symbol=None, params={}):
        raise ValueError('cancel_order not implemented')

    async def close(self, *args):
        return


class TestWriteGraph(TestCase):

    def test_write_graph_to_json(self):
        types = ['MultiDiGraph', 'MultiGraph', 'DiGraph', 'Graph']
        for t in types:
            g = getattr(nx, t)()
            d = format_graph_for_json(g)
            self.assertEqual(d['graph_type'], t)

        types = ['OrderedMultiDiGraph', 'OrderedMultiGraph', 'OrderedDiGraph']
        for t in types:
            g = getattr(nx, t)()
            with self.assertRaises(TypeError):
                d = format_graph_for_json(g)

            d = format_graph_for_json(g, raise_errors=False)
            self.assertEqual(d['graph_type'], 'other')


class TestSingleExchange(TestCase):

    def test_load_exchange_graph(self):
        currencies = ['BTC', 'ETH', 'USD', 'LTC']
        tickers = {
            'BTC/USD': {'bid': 5995, 'ask': 6000, 'bidVolume': 0.5, 'askVolume': 0.9},
            'ETH/BTC': {'bid': 0.069, 'ask': 0.07, 'bidVolume': 0.5, 'askVolume': 21},
            'ETH/USD': {'bid': 495, 'ask': 500, 'bidVolume': 30, 'askVolume': 0.9},
            'LTC/USD': {'bid': 81, 'ask': 82, 'bidVolume': 0.5, 'askVolume': 0.9},
            'LTC/BTC': {'bid': 0.121, 'ask': 0.122, 'bidVolume': 0.5, 'askVolume': 0.9},
            'LTC/ETH': {'bid': 90, 'ask': 100, 'bidVolume': 0.5, 'askVolume': 0.9}
        }
        symbols = [symbol for symbol in tickers.keys()]
        markets = {symbol: {'taker': 0.001} for symbol in symbols}
        exchange = TestExchange(name='a', currencies=currencies, tickers=tickers, symbols=symbols, markets=markets)

        graph = asyncio.get_event_loop().run_until_complete(
            load_exchange_graph(exchange, name=False,  fees=True, suppress=[''], depth=True, tickers=tickers))

        for symbol, quote_data in tickers.items():
            base, quote = symbol.split('/')
            self.assertEqual(graph[base][quote]['weight'], -math.log(quote_data['bid'] * (1 - markets[symbol]['taker'])))
            self.assertEqual(graph[base][quote]['depth'], -math.log(quote_data['bidVolume']))

            self.assertEqual(graph[quote][base]['weight'],
                             -math.log((1 - markets[symbol]['taker']) / quote_data['ask']))
            self.assertEqual(graph[quote][base]['depth'], -math.log(quote_data['askVolume'] * quote_data['ask']))

            self.assertEqual(symbol, graph[base][quote]['market_name'])
