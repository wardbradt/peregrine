import ccxt.async as ccxt
from .async_build_markets import get_exchanges_for_market
import asyncio


class OpportunityFinder:

    def __init__(self, market_name, exchanges=None, name=True):
        """
        An object of type OpportunityFinder finds the largest price disparity between exchanges for a given
        cryptocurrency market by finding the exchange with the lowest market ask price and the exchange with the
        highest market bid price.
        """
        if exchanges is None:
            if not name:
                raise ValueError("if parameter name == False, parameter exchanges cannot be None.")
            exchanges = get_exchanges_for_market(market_name)

        exchanges = [getattr(ccxt, exchange_id)() for exchange_id in exchanges]

        self.exchange_list = exchanges
        self.market_name = market_name
        self.highest_bid = {'exchange': None, 'price': -1}
        self.lowest_ask = {'exchange': None, 'price': 9999999}

    async def _test_bid_and_ask(self, exchange):
        """
        Retrieves the bid and ask for self.market_name on self.exchange_name. If the retrieved bid > self.highest_bid,
        sets self.highest_bid to the retrieved bid. If retrieved ask < self.lowest ask, sets self.lowest_ask to the
        retrieved ask.
        """
        if not isinstance(exchange, ccxt.Exchange):
            raise ValueError("exchange is not a ccxt Exchange instance.")

        try:
            ticker = await exchange.fetch_ticker(self.market_name)
        # A KeyError or ExchangeError occurs when the exchange does not have a market named self.market_name.
        # Any ccxt BaseError is because of ccxt, not this code.
        except (KeyError, ccxt.ExchangeError, ccxt.BaseError):
            await exchange.close()
            return

        await exchange.close()

        try:
            ask = ticker['ask']
            bid = ticker['bid']
        # ask and bid == None if this market is non existent.
        except TypeError:
            return

        if self.highest_bid['price'] < bid:
            self.highest_bid['price'] = bid
            self.highest_bid['exchange'] = exchange
        if ask < self.lowest_ask['price']:
            self.lowest_ask['price'] = ask
            self.lowest_ask['exchange'] = exchange

    async def find_min_max(self):
        tasks = [self._test_bid_and_ask(exchange_name) for exchange_name in self.exchange_list]
        await asyncio.wait(tasks)

        return {'highest_bid': self.highest_bid,
                'lowest_ask': self.lowest_ask}


async def get_opportunity_for_market(ticker, exchanges=None, name=True):
    finder = OpportunityFinder(ticker, exchanges=exchanges, name=name)
    return await finder.find_min_max()
