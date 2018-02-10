import ccxt.async as ccxt
import asyncio
from peregrine.utils import get_exchanges_for_market


class OpportunityFinder:

    def __init__(self, market_name, exchange_list=None):
        """
        An object of type OpportunityFinder finds the largest price disparity between exchanges for a given
        cryptocurrency market by finding the exchange with the lowest market ask price and the exchange with the
        highest market bid price.
        """
        if exchange_list is None:
            exchange_list = get_exchanges_for_market(market_name)

        self.exchange_list = exchange_list
        self.market_name = market_name
        self.highest_bid = {'exchange': None, 'amount': -1}
        self.lowest_ask = {'exchange': None, 'amount': 9999999}

    async def _test_bid_and_ask(self, exchange_name):
        """
        Retrieves the bid and ask for self.market_name on self.exchange_name. If the retrieved bid > self.highest_bid,
        sets self.highest_bid to the retrieved bid. If retrieved ask < self.lowest ask, sets self.lowest_ask to the
        retrieved ask.
        """
        exchange = getattr(ccxt, exchange_name)()
        try:
            order_book = await exchange.fetch_order_book(self.market_name)
        except ccxt.BaseError:
            return None
        bid = order_book['bids'][0][0] if len(order_book['bids']) > 0 else -1
        ask = order_book['asks'][0][0] if len(order_book['asks']) > 0 else 999999
        if self.highest_bid['amount'] < bid:
            self.highest_bid['amount'] = bid
            self.highest_bid['exchange'] = exchange
        if ask < self.lowest_ask['amount']:
            self.lowest_ask['amount'] = ask
            self.lowest_ask['exchange'] = exchange

    def find_min_max(self):
        futures = [asyncio.ensure_future(self._test_bid_and_ask(exchange_name)) for exchange_name in
                   self.exchange_list]
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*futures))

        return {'highest_bid': self.highest_bid,
                'lowest_ask': self.lowest_ask}


def get_opportunity_for_market(ticker, exchange_list=None):
    finder = OpportunityFinder(ticker, exchange_list)
    return finder.find_min_max()
