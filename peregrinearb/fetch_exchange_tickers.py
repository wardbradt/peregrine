import ccxt.async as ccxt
import asyncio
import networkx as nx
import time


class TickerFetcher:

    def __init__(self, exchange_names, name=True):
        """
        This could be used for when data is needed for both inter and intra exchange opportunity-finding to avoid
        pinging APIs twice for the same data.
        """
        if name:
            self.exchanges = [getattr(ccxt, exchange_name)() for exchange_name in exchange_names]
        else:
            self.exchanges = exchange_names

        self.ticker_dicts = {}

    async def fetch_exchange_tickers(self):
        tasks = [await self._fetch_exchange_tickers(exchange) for exchange in self.exchanges]
        await asyncio.wait(tasks)
        return self.ticker_dicts

    async def _fetch_exchange_tickers(self, exchange):
        self.ticker_dicts[exchange.id] = await exchange.fetch_tickers()


async def fetch_exchange_tickers(exchange_names, name=True):
    fetcher = TickerFetcher(exchange_names, name=name)
    return await fetcher.fetch_exchange_tickers()

b = ccxt.gdax()
print(asyncio.get_event_loop().run_until_complete(b.fetch_tickers()))
asyncio.get_event_loop().run_until_complete(b.close())
