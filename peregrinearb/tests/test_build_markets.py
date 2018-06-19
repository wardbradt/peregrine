from unittest import TestCase
from peregrinearb.async_build_markets import build_all_collections, build_specific_collections, build_collections, \
    build_arbitrage_graph_for_exchanges
import ccxt.async as ccxt
import asyncio


class TestCollectionBuilder(TestCase):

    def test_exchange_length(self):
        collections = build_all_collections(write=False)
        for exchange_list in collections.values():
            # check that all collections are more than one long
            self.assertGreater(len(exchange_list), 1)


class TestCollectionBuilders(TestCase):

    def test_errors_raised(self):
        with self.assertRaises(ValueError):
            # note the misspelling of "countries" as "contries"
            build_specific_collections(contries=['US'])

    def test_whitelist_blacklist(self):
        us_exchanges = build_specific_collections(countries=['US'])
        confirmed_us_exchanges = []
        for exchange_list in us_exchanges.values():
            for exchange_name in exchange_list:
                # so each exchange is only checked once.
                if exchange_name in confirmed_us_exchanges:
                    continue
                exchange = getattr(ccxt, exchange_name)()
                self.assertIn('US', exchange.countries)
                confirmed_us_exchanges.append(exchange_name)

        not_us_exchanges = build_specific_collections(countries=['US'], blacklist=True)
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
        specific_collections = build_specific_collections(has={'fetchOrderBook': True, 'createOrder': True})
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
        collections = build_collections(write=False)
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
        graph = build_arbitrage_graph_for_exchanges(exchanges)
        for node in graph:
            self.assertGreater(graph.degree(node), 1)

    def test_market_names_of_edges_are_valid(self):
        exchange_names = ['bittrex', 'bitstamp', 'poloniex']
        graph = build_arbitrage_graph_for_exchanges(exchange_names)

        # load the exchanges with their markets
        exchanges = {exchange_name: getattr(ccxt, exchange_name)() for exchange_name in exchange_names}
        futures = [asyncio.ensure_future(exchange.load_markets()) for exchange in exchanges.values()]
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*futures))

        for edge in graph.edges(data=True):
            data = edge[2]
            exchange = exchanges[data['exchange_name']]
            self.assertIn(data['market_name'], exchange.symbols)
