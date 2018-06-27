import asyncio
import aiohttp
import logging
from peregrinearb.settings import LOGGING_PATH


class TickerGatherer:

    def __init__(self, endpoint, markets=None):
        self.logger = logging.getLogger(LOGGING_PATH + __name__)
        self.logger.debug('Initializing TickerGatherer')
        if markets is None:
            raise ValueError('markets cannot be none for class TickerGatherer. It is possible that a subclass of '
                             'TickerGatherer did not correctly implement the inheritance.')

        self.endpoint = endpoint
        self.markets = markets
        self.tickers = {}

    async def fetch_tickers(self):
        self.logger.info('Fetching tickers')
        tasks = [self._fetch_ticker(market) for market in self.markets]
        await asyncio.wait(tasks)
        self.logger.info('Fetched tickers')
        return self.tickers

    async def _fetch_ticker(self, market):
        ticker_endpoint = self.endpoint.format(market)
        self.logger.debug('Fetching ticker for {} at {}'.format(market, ticker_endpoint))
        async with aiohttp.ClientSession() as session:
            async with session.get(ticker_endpoint) as resp:
                self.tickers[market] = await resp.json()
        self.logger.debug('Fetched ticker for {} at {}'.format(market, ticker_endpoint))

    def format_tickers(self):
        raise ValueError('format_tickers not implemented in class TickerGatherer. To use, inherit from TickerGatherer '
                         'and override this function.')
