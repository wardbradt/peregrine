import ccxt.async as ccxt
from .async_build_markets import get_exchanges_for_market
import asyncio
import logging
from .settings import LOGGING_PATH


file_logger = logging.getLogger(LOGGING_PATH + __name__)


class OpportunityFinder:

    def __init__(self, market_name, exchanges=None, name=True):
        """
        An object of type OpportunityFinder finds the largest price disparity between exchanges for a given
        cryptocurrency market by finding the exchange with the lowest market ask price and the exchange with the
        highest market bid price.
        """
        self.logger = logging.getLogger(LOGGING_PATH + __name__)
        self.logger.debug('Initializing OpportunityFinder for {}'.format(market_name))

        if exchanges is None:
            self.logger.warning('Parameter name\'s being false has no effect.')
            exchanges = get_exchanges_for_market(market_name)

        if name:
            exchanges = [getattr(ccxt, exchange_id)() for exchange_id in exchanges]

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
        self.logger.info('Fetching ticker from {} for {}'.format(exchange.id, self.market_name))
        ticker = await exchange.fetch_ticker(self.market_name)
        self.logger.info('Fetched ticker from {} for {}'.format(exchange.id, self.market_name))
        # A KeyError or ExchangeError occurs when the exchange does not have a market named self.market_name.
        # Any ccxt BaseError is because of ccxt, not this code.
        # except (KeyError, ccxt.ExchangeError, ccxt.BaseError):
        #     await exchange.close()
        #     return

        self.logger.info('Closing connection to {}'.format(exchange.id))
        await exchange.close()
        self.logger.info('Closed connection to {}'.format(exchange.id))

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


class SuperOpportunityFinder:

    def __init__(self, exchanges, collections, name=True):
        """
        SuperOpportunityFinder, given a dict of collections, yields opportunities in the order they come. There is not
        enough overlap between SuperOpportunityFinder and OpportunityFinder to warrant inheritance.

        The sometimes-odd structure of this class is to ensure that connections to exchanges' servers are closed. It
        is structured so because Python's pass-by-object reference can lead to new instances of exchanges (with unclosed
        connections).

        :param exchanges: A list of exchanges, either ccxt.Exchange objects or names of exchanges
        :param collections: A dict of collections, as returned by CollectionBuilder in async_build_markets.py
        :param name: True if exchanges is a list of strings, False if it is a list of ccxt.Exchange objects
        """
        self.logger = logging.getLogger(LOGGING_PATH + __name__)
        self.logger.debug('Initializing SuperOpportunityFinder')
        if name:
            self.exchanges = {e: getattr(ccxt, e)() for e in exchanges}
        else:
            self.exchanges = {e.id: e for e in exchanges}
        self.collections = collections
        self.logger.debug('Initialized SuperOpportunityFinder')
        self.rate_limited_exchanges = set()

    async def get_opportunities(self):
        self.logger.info('Finding inter-exchange opportunities.')
        tasks = [self._find_opportunity(market_name, exchange_list)
                 for market_name, exchange_list in self.collections.items()]

        for result in asyncio.as_completed(tasks):
            yield await result

        tasks = [e.close() for e in self.exchanges.values()]
        await asyncio.wait(tasks)
        self.logger.info('Yielded all inter-exchange opportunities.')

    async def _find_opportunity(self, market_name, exchange_list):
        # Try again in one second if any of these exchanges are currently rate limited.
        for e in exchange_list:
            if e in self.rate_limited_exchanges:
                await asyncio.sleep(0.45)
                return await self._find_opportunity(market_name, exchange_list)

        self.logger.info('Finding opportunity for {}'.format(market_name))
        opportunity = {'highest_bid': {'price': -1, 'exchange': None},
                       'lowest_ask': {'price': float('Inf'), 'exchange': None},
                       'ticker': market_name}

        tasks = [self.exchange_fetch_ticker(exchange_name, market_name) for exchange_name in exchange_list]
        for res in asyncio.as_completed(tasks):
            ticker, exchange_name = await res
            # If fetch_ticker() caused a ccxt.ExchangeNotAvailable error
            if exchange_name is None:
                continue
            # Cannot catch Exception at this level because of asyncio, so if ticker is None, that means there was either
            # a RequestTimeout or DDosProtection error.
            if ticker is None:
                self.rate_limited_exchanges.add(exchange_name)
                await asyncio.sleep(1.2)
                # Because of asynchronicity, error.exchange_name may no longer be in self.rate_limited_exchanges
                if exchange_name in self.rate_limited_exchanges:
                    self.rate_limited_exchanges.remove(exchange_name)

                return await self._find_opportunity(market_name, exchange_list)

            if ticker['bid'] == 0 or ticker['ask'] == 0:
                continue

            try:
                if ticker['bid'] > opportunity['highest_bid']['price']:
                    opportunity['highest_bid']['price'] = ticker['bid']
                    opportunity['highest_bid']['exchange'] = exchange_name

                if ticker['ask'] < opportunity['lowest_ask']['price']:
                    opportunity['lowest_ask']['price'] = ticker['bid']
                    opportunity['lowest_ask']['exchange'] = exchange_name
            # If ticker['bid'] or ticker['ask'] == None because of incredibly low volume
            except TypeError:
                continue

        self.logger.info('Found opportunity for {}'.format(market_name))
        return opportunity

    async def exchange_fetch_ticker(self, exchange_name, market_name):
        """
        Returns a two-tuple structured as (ticker, exchange_name)
        """
        self.logger.debug('Fetching ticker from {} for {}'.format(exchange_name, market_name))
        try:
            ticker = await self.exchanges[exchange_name].fetch_ticker(market_name)
        except ccxt.DDoSProtection:
            self.logger.warning('Rate limited on {} for {} inter-exchange opportunity.'.format(exchange_name,
                                                                                               market_name))
            return None, exchange_name
        except ccxt.RequestTimeout:
            self.logger.warning('Request timeout on {} for {} inter-exchange opportunity.'.format(exchange_name,
                                                                                                  market_name))
            return None, exchange_name
        except ccxt.ExchangeNotAvailable:
            self.logger.warning('Fetching {} on {} raised an ExchangeNotAvailable error.'.format(exchange_name,
                                                                                                 market_name))
            return None, None

        self.logger.debug('Fetched ticker from {} for {}'.format(exchange_name, market_name))
        return ticker, exchange_name


def get_opportunities_for_collection(exchanges, collections, name=True):
    finder = SuperOpportunityFinder(exchanges, collections, name=name)
    return finder.get_opportunities()


async def get_opportunity_for_market(ticker, exchanges=None, name=True):
    file_logger.info('Finding lowest ask and highest bid for {}'.format(ticker))
    finder = OpportunityFinder(ticker, exchanges=exchanges, name=name)
    result = await finder.find_min_max()
    file_logger.info('Found lowest ask and highest bid for {}'.format(ticker))
    return result
