import networkx as nx
import asyncio
import ccxt.async_support as ccxt
import json
from .settings import COLLECTIONS_DIR

__all__ = [
    'ExchangeMultiGraphBuilder',
    'build_arbitrage_graph_for_exchanges',
    'build_multi_graph_for_exchanges',
]


class ExchangeMultiGraphBuilder:

    def __init__(self, exchanges: list):
        self.exchanges = exchanges
        self.graph = nx.MultiGraph()

    async def build_multi_graph(self, write=False, ccxt_errors=True):
        await asyncio.wait([self._add_exchange_to_graph(exchange_name, ccxt_errors) for
                 exchange_name in self.exchanges])

        if write:
            with open(COLLECTIONS_DIR + 'graph.json', 'w') as outfile:
                json.dump(self.graph, outfile)

        return self.graph

    async def _add_exchange_to_graph(self, exchange_name: str, ccxt_errors=True):
        """
        :param ccxt_errors: if true, raises errors ccxt raises when calling load_markets. The common ones are
        RequestTimeout and ExchangeNotAvailable, which are caused by problems with exchanges' APIs.
        """
        exchange = getattr(ccxt, exchange_name)()
        if ccxt_errors:
            await exchange.load_markets()
            await exchange.close()
        else:
            try:
                await exchange.load_markets()
                await exchange.close()
            except ccxt.BaseError:
                await exchange.close()
                return

        for market_name in exchange.symbols:
            currencies = market_name.split('/')

            try:
                self.graph.add_edge(currencies[0], currencies[1], exchange_name=exchange_name, market_name=market_name)
            # certain exchanges (lykke, possibly more)
            except IndexError as e:
                pass


async def build_multi_graph_for_exchanges(exchanges: list, **kwargs):
    """
    A wrapper function for the usage of the ExchangeMultiGraphBuilder class which returns a dict as specified in the
    docstring of __init__ in ExchangeMultiGraphBuilder.
    :param exchanges: A list of exchanges (e.g. ['bittrex', 'poloniex', 'bitstamp', 'anxpro']
    """
    return await ExchangeMultiGraphBuilder(exchanges).build_multi_graph(**kwargs)


async def build_arbitrage_graph_for_exchanges(exchanges: list):
    """
    This function is currently inefficient as it finds the entire graph for the given exchanges then finds the k-core
    for that graph. todo: It would be great if someone could improve the efficiency of it but this is not a priority.

    IMPORTANT: For this function to work, the @not_implemented_for('multigraph') decorator above the core_number
    function in networkx.algorithms.core.py must be removed or commented out.
    Todo: Improve this project so that the above does not have to be done.

    :param exchanges: A list of exchanges (e.g. ['bittrex', 'poloniex', 'bitstamp', 'gdax']
    """
    return nx.k_core(build_multi_graph_for_exchanges(exchanges), 2)
