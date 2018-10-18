import ccxt.async_support as ccxt
import asyncio
import logging
__all__ = [
    'BulkTickerFetcher',
    'fetch_exchange_tickers',
]

logger = logging.getLogger('peregrinearb.fetch_exchange_tickers')


class BulkTickerFetcher:

    def __init__(self, exchange_names, name=True, invocation_count=0):
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
        logger.info('Fetching exchange tickers')
        tasks = [self._fetch_exchange_tickers(exchange) for exchange in self.exchanges]
        await asyncio.wait(tasks)
        logger.info('Fetched exchange tickers')
        return self.ticker_dicts

    async def _fetch_exchange_tickers(self, exchange):
        logger.info('Exchange#{} - Fetching tickers'.format(exchange.id))
        self.ticker_dicts[exchange.id] = await exchange.fetch_tickers()
        await exchange.close()
        logger.info('Exchange#{} - Fetched tickers'.format(exchange.id))


async def fetch_exchange_tickers(exchange_names, name=True, count=0):
    fetcher = BulkTickerFetcher(exchange_names, name=name, invocation_count=count)
    return await fetcher.fetch_exchange_tickers()
