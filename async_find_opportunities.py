import ccxt.async as ccxt
import asyncio
import json


class SingularlyAvailableExchangeError(Exception):
    def __init__(self, market_ticker):
        super(SingularlyAvailableExchangeError, self).__init__("{} is available on only one exchange."
                                                               .format(market_ticker))


class InvalidExchangeError(Exception):
    def __init__(self, market_ticker):
        super(InvalidExchangeError, self).__init__("{} is either an invalid exchange or has a broken API."
                                                   .format(market_ticker))


def get_exchange_pairs_for_market(market_ticker):
    with open('collections.json') as f:
        collections = json.load(f)
    for market_name, exchanges in collections.items():
        if market_name == market_ticker:
            return exchanges

    with open('singularly_available_markets.json') as f:
        singularly_available_markets = json.load(f)
    for market_name, exchange in singularly_available_markets:
        if market_name == market_ticker:
            raise SingularlyAvailableExchangeError(market_ticker)

    raise InvalidExchangeError(market_ticker)


class OpportunityFinder:

    def __init__(self, market_name, exchange_list=None):
        """
        An object of type OpportunityFinder finds the largest price disparity between exchanges for a given
        cryptocurrency market by finding the exchange with the lowest market ask price and the exchange with the
        highest market bid price.
        :param market_name:
        :param exchange_list:
        """
        if exchange_list is None:
            exchange_list = get_exchange_pairs_for_market(market_name)

        self.exchange_list = exchange_list
        self.market_name = market_name
        self.highest_bid = {'exchange': None, 'amount': -1}
        self.lowest_ask = {'exchange': None, 'amount': 9999999}

    async def test_bid_and_ask(self, exchange_name):
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
        futures = [asyncio.ensure_future(self.test_bid_and_ask(exchange_name)) for exchange_name in
                   self.exchange_list]
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*futures))

        return {'highest_bid': self.highest_bid,
                'lowest_ask': self.lowest_ask}
