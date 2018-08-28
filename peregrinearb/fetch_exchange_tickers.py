import ccxt.async_support as ccxt
import asyncio
import logging
from peregrinearb.settings import LOGGING_PATH


class BulkTickerFetcherAdapter(logging.LoggerAdapter):
    def __init__(self, logger, extra):
        super(BulkTickerFetcherAdapter, self).__init__(logger, extra)

    def process(self, msg, kwargs):
        return 'Invocation#{} - {}'.format(self.extra['count'], msg), kwargs


class BulkTickerFetcher:

    def __init__(self, exchange_names, name=True, invocation_count=0):
        """
        This could be used for when data is needed for both inter and intra exchange opportunity-finding to avoid
        pinging APIs twice for the same data.
        """
        logger = logging.getLogger(LOGGING_PATH + __name__)
        self.adapter = BulkTickerFetcherAdapter(logger, {'count': invocation_count})
        if name:
            self.exchanges = [getattr(ccxt, exchange_name)() for exchange_name in exchange_names]
        else:
            self.exchanges = exchange_names

        self.ticker_dicts = {}

    async def fetch_exchange_tickers(self):
        self.adapter.info('Fetching exchange tickers')
        tasks = [self._fetch_exchange_tickers(exchange) for exchange in self.exchanges]
        await asyncio.wait(tasks)
        self.adapter.info('Fetched exchange tickers')
        return self.ticker_dicts

    async def _fetch_exchange_tickers(self, exchange):
        self.adapter.info('Exchange#{} - Fetching tickers'.format(exchange.id))
        self.ticker_dicts[exchange.id] = await exchange.fetch_tickers()
        await exchange.close()
        self.adapter.info('Exchange#{} - Fetched tickers'.format(exchange.id))


async def fetch_exchange_tickers(exchange_names, name=True, count=0):
    fetcher = BulkTickerFetcher(exchange_names, name=name, invocation_count=count)
    return await fetcher.fetch_exchange_tickers()
