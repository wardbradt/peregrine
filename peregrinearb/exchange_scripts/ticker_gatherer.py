import asyncio
import aiohttp


class TickerGatherer:

    def __init__(self, endpoint, markets=None):
        if markets is None:
            raise ValueError('markets cannot be none for class TickerGatherer. It is possible that a subclass of '
                             'TickerGatherer did not correctly implement the inheritance.')

        self.endpoint = endpoint
        self.markets = markets
        self.tickers = {}

    async def fetch_tickers(self):
        tasks = [self._fetch_ticker(market) for market in self.markets]
        await asyncio.wait(tasks)
        return self.tickers

    async def _fetch_ticker(self, market):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.endpoint.format(market)) as resp:
                self.tickers[market] = await resp.json()

    def format_tickers(self):
        raise ValueError('format_tickers not implemented in class TickerGatherer. To use, inherit from TickerGatherer and'
                         'override this function.')
