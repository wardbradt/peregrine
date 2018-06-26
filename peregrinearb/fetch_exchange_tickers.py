import ccxt.async as ccxt
import asyncio
import logging


class BulkTickerFetcher:

    def __init__(self, exchange_names, name=True):
        """
        This could be used for when data is needed for both inter and intra exchange opportunity-finding to avoid
        pinging APIs twice for the same data.
        """
        self.logger = logging.getLogger(__name__)
        if name:
            self.exchanges = [getattr(ccxt, exchange_name)() for exchange_name in exchange_names]
        else:
            self.exchanges = exchange_names

        self.ticker_dicts = {}

    async def fetch_exchange_tickers(self):
        self.logger.info('Fetching exchange tickers')
        tasks = [self._fetch_exchange_tickers(exchange) for exchange in self.exchanges]
        await asyncio.wait(tasks)
        return self.ticker_dicts

    async def _fetch_exchange_tickers(self, exchange):
        self.logger.info('Fetching tickers for {}'.format(exchange.id))
        self.ticker_dicts[exchange.id] = await exchange.fetch_tickers()
        await exchange.close()
        self.logger.info('Finished fetching tickers for {}'.format(exchange.id))


async def fetch_exchange_tickers(exchange_names, name=True):
    fetcher = BulkTickerFetcher(exchange_names, name=name)
    return await fetcher.fetch_exchange_tickers()
