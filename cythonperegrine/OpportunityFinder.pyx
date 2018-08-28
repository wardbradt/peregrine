import ccxt.async_support as ccxt
import asyncio
import json


cdef class SingularlyAvailableExchangeError(Exception):
    def __init__(self, market_ticker):
        super(SingularlyAvailableExchangeError, self).__init__("{} is available on only one exchange.".format(market_ticker))


cdef class InvalidExchangeError(Exception):
    def __init__(self, market_ticker):
        super(InvalidExchangeError, self).__init__("{} is either an invalid exchange or has a broken API.".format(market_ticker))


cpdef get_exchange_pairs_for_market(market_ticker):
    with open('cythongperegrine/collections/collections.json') as f:
        collections = json.load(f)
    for market_name, exchanges in collections.items():
        if market_name == market_ticker:
            return exchanges

    with open('cythongperegrine/collections/singularly_available_markets.json') as f:
        singularly_available_markets = json.load(f)
    for market_name, exchange in singularly_available_markets:
        if market_name == market_ticker:
            raise SingularlyAvailableExchangeError(market_ticker)

    raise InvalidExchangeError(market_ticker)


cdef class OpportunityFinder:

    def __cinit__(self, str market_name, list exchange_list=None):
        """
        An object of type OpportunityFinder finds the largest price disparity between exchanges for a given
        cryptocurrency market by finding the exchange with the lowest market ask price and the exchange with the
        highest market bid price.
        """
        if exchange_list is None:
            exchange_list = get_exchange_pairs_for_market(market_name)

        self.exchange_list = exchange_list
        # coerce market_name from python str to C char*
        py_byte_string = market_name.encode('UTF-8')
        self.market_name = py_byte_string

        cdef bid highest_bid
        highest_bid.exchange_name = ''
        highest_bid.price = -1
        self.highest_bid = highest_bid

        cdef bid lowest_ask
        lowest_ask.exchange_name = ''
        lowest_ask.price = 9999999
        self.lowest_ask = lowest_ask

    # todo: can we do 'async cpdef'?
    async def test_bid_and_ask(self, exchange_name):
        """
        Retrieves the bid and ask for self.market_name on self.exchange_name. If the retrieved bid > self.highest_bid,
        sets self.highest_bid to the retrieved bid. If retrieved ask < self.lowest ask, sets self.lowest_ask to the
        retrieved ask.
        """
        exchange = getattr(ccxt, exchange_name)()
        market_name = self.market_name.decode('utf-8')
        try:
            # ccxt expects a str as the first argument for fetch_order_book. self.market_name is a byte string so it
            # must be decoded to a str.
            order_book = await exchange.fetch_order_book(market_name)
        except ccxt.BaseError:
            return None
        cdef float bid = order_book['bids'][0][0] if len(order_book['bids']) > 0 else -1
        cdef float ask = order_book['asks'][0][0] if len(order_book['asks']) > 0 else 999999
        if self.highest_bid.price < bid:
            self.highest_bid.price = bid
            self.highest_bid.exchange_name = exchange
        if ask < self.lowest_ask.price:
            self.lowest_ask.price = ask
            self.lowest_ask.exchange_name = exchange

    cpdef find_min_max(self):
        futures = [asyncio.ensure_future(self.test_bid_and_ask(exchange_name)) for exchange_name in
                   self.exchange_list]
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*futures))

        return {'highest_bid': self.highest_bid,
                'lowest_ask': self.lowest_ask}
