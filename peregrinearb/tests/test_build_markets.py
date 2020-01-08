from unittest import TestCase
from peregrinearb.async_build_markets import build_collections, build_specific_collections, SymbolCollectionBuilder
import ccxt.async_support as ccxt
import asyncio
from peregrinearb.multi_graph_builder import build_arbitrage_graph_for_exchanges


class TestCollectionBuilders(TestCase):

    def test_errors_raised(self):
        with self.assertRaises(ValueError):
            # note the misspelling of "countries" as "contries"
            build_specific_collections(contries=['US'])

    def test_whitelist_blacklist(self):
        us_exchanges = asyncio.get_event_loop().run_until_complete(build_specific_collections(countries=['US']))
        confirmed_us_exchanges = []
        for exchange_list in us_exchanges.values():
            for exchange_name in exchange_list:
                # so each exchange is only checked once.
                if exchange_name in confirmed_us_exchanges:
                    continue
                exchange = getattr(ccxt, exchange_name)()
                self.assertIn('US', exchange.countries)
                confirmed_us_exchanges.append(exchange_name)

        not_us_exchanges = asyncio.get_event_loop().run_until_complete(
            build_specific_collections(countries=['US'], blacklist=True)
        )
        confirmed_not_us_exchanges = []
        for exchange_list in not_us_exchanges.values():
            for exchange_name in exchange_list:
                # so each exchange is only checked once.
                if exchange_name in confirmed_not_us_exchanges:
                    continue
                exchange = getattr(ccxt, exchange_name)()
                self.assertNotIn('US', exchange.countries)
                confirmed_not_us_exchanges.append(exchange_name)

    def test_kwargs_with_dict_as_rule(self):
        specific_collections = asyncio.get_event_loop().run_until_complete(
            build_specific_collections(has={'fetchOrderBook': True, 'createOrder': True})
        )
        # exchanges which are confirmed to meet the given criteria (.hasFetchOrderBook and .hasCreateOrder)
        confirmed_exchanges = []
        for exchange_list in specific_collections.values():
            for exchange_name in exchange_list:
                if exchange_name in confirmed_exchanges:
                    continue
                exchange = getattr(ccxt, exchange_name)()
                self.assertTrue(exchange.hasFetchOrderBook and exchange.hasCreateOrder)
                confirmed_exchanges.append(exchange_name)

    def test_build_collections(self):
        collections = asyncio.get_event_loop().run_until_complete(build_collections(write=False))
        confirmed_exchanges = []
        for exchange_list in collections.values():
            for exchange_name in exchange_list:
                if exchange_name in confirmed_exchanges:
                    continue
                exchange = getattr(ccxt, exchange_name)()
                self.assertTrue(exchange.has['fetchOrderBook'])
                confirmed_exchanges.append(exchange_name)


class TestExchangeGraphBuilder(TestCase):

    def test_all_node_degrees_greater_than_one(self):
        exchanges = ['bittrex', 'bitstamp', 'poloniex']
        graph = asyncio.get_event_loop().run_until_complete(build_arbitrage_graph_for_exchanges(exchanges))
        for node in graph:
            self.assertGreater(graph.degree(node), 1)

    def test_market_names_of_edges_are_valid(self):
        exchange_names = ['bittrex', 'bitstamp', 'poloniex']
        graph = asyncio.get_event_loop().run_until_complete(build_arbitrage_graph_for_exchanges(exchange_names))

        # load the exchanges with their markets
        exchanges = {exchange_name: getattr(ccxt, exchange_name)() for exchange_name in exchange_names}
        futures = [asyncio.ensure_future(exchange.load_markets()) for exchange in exchanges.values()]
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*futures))

        for edge in graph.edges(data=True):
            data = edge[2]
            exchange = exchanges[data['exchange_name']]
            self.assertIn(data['market_name'], exchange.symbols)


class TestExchange(ccxt.Exchange):

    def __init__(self, name='', markets=None):
        super().__init__()
        if markets is None:
            markets = {}
        self.markets = markets
        self.id = name

    @property
    def symbols(self):
        return self.markets.keys()

    @property
    def currencies(self):
        result = set()
        for market in self.markets:
            try:
                base, quote = market.split('/')
            except ValueError:
                continue
            result.add(base)
            result.add(quote)
        return result

    async def load_markets(self, reload=False):
        pass


class SymbolCollectionBuilderTestCase(TestCase):

    def test_add_exchange_to_symbol(self):
        exchange_a = TestExchange(name='a', )
        exchange_b = TestExchange(name='b', )

        builder = SymbolCollectionBuilder([exchange_a, exchange_b], )
        self.assertEqual(builder.collections, {})
        builder._add_exchange_to_symbol('A/B', 'a')
        self.assertEqual(builder.collections, {'A/B': ['a']})
        builder._add_exchange_to_symbol('A/B', 'a')
        self.assertEqual(builder.collections, {'A/B': ['a']})

        builder._add_exchange_to_symbol('A/B', 'b')
        self.assertEqual(builder.collections, {'A/B': ['a', 'b']})

        builder._add_exchange_to_symbol('B/C', 'b')
        self.assertEqual(builder.collections, {'A/B': ['a', 'b'], 'B/C': ['b']})

        asyncio.get_event_loop().run_until_complete(exchange_a.close())
        asyncio.get_event_loop().run_until_complete(exchange_b.close())

    def test_add_exchange_to_collections(self):
        exchange_a = TestExchange(name='a', markets={sym: {} for sym in ['A/B', 'A/C', 'B/C', 'E/C']})
        exchange_b = TestExchange(name='b', markets={sym: {} for sym in ['A/B', 'D/C', 'B/C', 'E/A', 'A/X']})

        builder = SymbolCollectionBuilder([exchange_a, exchange_b],
                                          symbols=['D/C'],
                                          exclusive_currencies=['B', 'X', 'C'],
                                          inclusive_currencies=['D'], )

        result = asyncio.get_event_loop().run_until_complete(builder.build_collections(write=False, ))
        print(result)
        self.assertEqual(result, {'B/C': ['a', 'b'], 'D/C': ['b']})
