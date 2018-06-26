import ccxt.async as ccxt
from .async_build_markets import get_exchanges_for_market
import asyncio
import logging


file_logger = logging.getLogger(__name__)


class OpportunityFinder:

    def __init__(self, market_name, exchanges=None, name=True, close=True):
        """
        An object of type OpportunityFinder finds the largest price disparity between exchanges for a given
        cryptocurrency market by finding the exchange with the lowest market ask price and the exchange with the
        highest market bid price.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Initializing OpportunityFinder for {}'.format(market_name))

        if exchanges is None:
            file_logger.warning('Parameter name\'s being false has no effect.')
            exchanges = get_exchanges_for_market(market_name)

        if name:
            exchanges = [getattr(ccxt, exchange_id)() for exchange_id in exchanges]

        self.close = close
        self.exchange_list = exchanges
        self.market_name = market_name
        self.highest_bid = {'exchange': None, 'price': -1}
        self.lowest_ask = {'exchange': None, 'price': float('Inf')}
        self.logger.debug('Initialized OpportunityFinder for {}'.format(market_name))

    async def _test_bid_and_ask(self, exchange):
        """
        Retrieves the bid and ask for self.market_name on self.exchange_name. If the retrieved bid > self.highest_bid,
        sets self.highest_bid to the retrieved bid. If retrieved ask < self.lowest ask, sets self.lowest_ask to the
        retrieved ask.
        """
        self.logger.info('Checking if {} qualifies for the highest bid or lowest ask for {}'.format(exchange.id,
                                                                                                    self.market_name))
        if not isinstance(exchange, ccxt.Exchange):
            raise ValueError("exchange is not a ccxt Exchange instance.")

        # try:
        self.logger.debug('Fetching ticker from {} for {}'.format(exchange.id, self.market_name))
        ticker = await exchange.fetch_ticker(self.market_name)
        self.logger.debug('Fetched ticker from {} for {}'.format(exchange.id, self.market_name))
        # A KeyError or ExchangeError occurs when the exchange does not have a market named self.market_name.
        # Any ccxt BaseError is because of ccxt, not this code.
        # except (KeyError, ccxt.ExchangeError, ccxt.BaseError):
        #     await exchange.close()
        #     return

        if self.close:
            self.logger.debug('Closing connection to {}'.format(exchange.id))
            await exchange.close()
            self.logger.debug('Closed connection to {}'.format(exchange.id))

        ask = ticker['ask']
        bid = ticker['bid']

        if self.highest_bid['price'] < bid:
            self.highest_bid['price'] = bid
            self.highest_bid['exchange'] = exchange
        if ask < self.lowest_ask['price']:
            self.lowest_ask['price'] = ask
            self.lowest_ask['exchange'] = exchange
        self.logger.info('Checked if {} qualifies for the highest bid or lowest ask for {}'.format(exchange.id,
                                                                                                   self.market_name))

    async def find_min_max(self):
        tasks = [self._test_bid_and_ask(exchange_name) for exchange_name in self.exchange_list]
        await asyncio.wait(tasks)

        return {'highest_bid': self.highest_bid,
                'lowest_ask': self.lowest_ask,
                'ticker': self.market_name}


async def get_opportunity_for_market(ticker, exchanges=None, name=True, close=True):
    file_logger.info('Finding lowest ask and highest bid for {}'.format(ticker))
    finder = OpportunityFinder(ticker, exchanges=exchanges, name=name, close=close)
    result = await finder.find_min_max()
    file_logger.info('Found lowest ask and highest bid for {}'.format(ticker))
    return result
