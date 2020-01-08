import ccxt.async_support as ccxt
from .async_build_markets import get_exchanges_for_market
import asyncio
import logging
from .settings import INTER_LOGGING_PATH
import datetime
from .utils import Collections
from .utils.logging_utils import FormatForLogAdapter

__all__ = [
    'OpportunityFinder',
    'SuperOpportunityFinder',
    'get_opportunity_for_market',
    'get_opportunities_for_collection',
]

file_logger = logging.getLogger(INTER_LOGGING_PATH + __name__)


class InterExchangeAdapter(logging.LoggerAdapter):

    def __init__(self, logger, extra):
        super(InterExchangeAdapter, self).__init__(logger, extra)

    def process(self, msg, kwargs):
        return 'Invocation#{} - Market#{} - {}'.format(self.extra['invocation_id'], self.extra['market'], msg), kwargs


__all__ = [
    'OpportunityFinder',
    'get_opportunity_for_market'
]


class OpportunityFinder:

    def __init__(self, market_name, exchanges=None, name=True, invocation_id=0):
        """
        An object of type OpportunityFinder finds the largest price disparity between exchanges for a given
        cryptocurrency market by finding the exchange with the lowest market ask price and the exchange with the
        highest market bid price.
        """
        logger = logging.getLogger(INTER_LOGGING_PATH + __name__)
        self.adapter = InterExchangeAdapter(logger, {'invocation_id': invocation_id, 'market': market_name})
        self.adapter.debug('Initializing OpportunityFinder for {}'.format(market_name))

        if exchanges is None:
            self.adapter.warning('Parameter name\'s being false has no effect.')
            exchanges = get_exchanges_for_market(market_name)

        if name:
            exchanges = [getattr(ccxt, exchange_id)() for exchange_id in exchanges]

        self.exchange_list = exchanges
        self.market_name = market_name
        self.highest_bid = {'exchange': None, 'price': -1}
        self.lowest_ask = {'exchange': None, 'price': float('Inf')}
        self.adapter.debug('Initialized OpportunityFinder for {}'.format(market_name))

    async def _test_bid_and_ask(self, exchange):
        """
        Retrieves the bid and ask for self.market_name on self.exchange_name. If the retrieved bid > self.highest_bid,
        sets self.highest_bid to the retrieved bid. If retrieved ask < self.lowest ask, sets self.lowest_ask to the
        retrieved ask.
        """
        self.adapter.info('Checking if {} qualifies for the highest bid or lowest ask for {}'.format(exchange.id,
                                                                                                     self.market_name))
        if not isinstance(exchange, ccxt.Exchange):
            raise ValueError("exchange is not a ccxt Exchange instance.")

        # try:
        self.adapter.info('Fetching ticker from {} for {}'.format(exchange.id, self.market_name))
        ticker = await exchange.fetch_ticker(self.market_name)
        self.adapter.info('Fetched ticker from {} for {}'.format(exchange.id, self.market_name))
        # A KeyError or ExchangeError occurs when the exchange does not have a market named self.market_name.
        # Any ccxt BaseError is because of ccxt, not this code.
        # except (KeyError, ccxt.ExchangeError, ccxt.BaseError):
        #     await exchange.close()
        #     return

        self.adapter.debug('Closing connection to {}'.format(exchange.id))
        await exchange.close()
        self.adapter.debug('Closed connection to {}'.format(exchange.id))

        ask = ticker['ask']
        bid = ticker['bid']

        if self.highest_bid['price'] < bid:
            self.highest_bid['price'] = bid
            self.highest_bid['exchange'] = exchange
        if ask < self.lowest_ask['price']:
            self.lowest_ask['price'] = ask
            self.lowest_ask['exchange'] = exchange
        self.adapter.info('Checked if exchange qualifies for the highest bid or lowest ask for market',
                          exchange=exchange.id, symbol=self.market_name)

    async def find_min_max(self):
        tasks = [self._test_bid_and_ask(exchange_name) for exchange_name in self.exchange_list]
        await asyncio.wait(tasks)

        return {'highest_bid': self.highest_bid,
                'lowest_ask': self.lowest_ask,
                'ticker': self.market_name}


class SuperInterExchangeAdapter(logging.LoggerAdapter):

    def __init__(self, logger, extra):
        super(SuperInterExchangeAdapter, self).__init__(logger, extra)

    def process(self, msg, kwargs):
        return 'Invocation#{} - {}'.format(self.extra['invocation_id'], msg), kwargs


class SuperOpportunityFinder:

    def __init__(self, exchanges, collections, name=True, opportunity_id=0, get_usd_rates=False,
                 opportunity_interval=0.05):
        """
        SuperOpportunityFinder, given a dict of collections, yields opportunities in the order they come. There is not
        enough overlap between SuperOpportunityFinder and OpportunityFinder to warrant inheritance.

        The sometimes-odd structure of this class is to ensure that connections to exchanges' servers are closed. It
        is structured so because Python's pass-by-object reference can lead to new instances of exchanges (with unclosed
        connections).

        :param exchanges: A list of exchanges, either ccxt.Exchange objects or names of exchanges
        :param collections: A dict of collections, as returned by CollectionBuilder in async_build_markets.py. The
        self.collections field will be a Collections object.
        :param name: True if exchanges is a list of strings, False if it is a list of ccxt.Exchange objects
        """
        self.adapter = FormatForLogAdapter(
            logging.getLogger('peregrinearb.async_find_opportunities.SuperOpportunityFinder'))
        self.adapter.debug('Initializing SuperOpportunityFinder')
        if name:
            self.exchanges = {e: getattr(ccxt, e)() for e in exchanges}
        else:
            self.exchanges = {e.id: e for e in exchanges}
        self.collections = Collections(collections)
        self.adapter.debug('Initialized SuperOpportunityFinder')
        self.rate_limited_exchanges = set()
        self._find_opportunity_calls = -1
        # starting opportunity id for logging
        self.opportunity_id = opportunity_id
        self.usd_rates = {}
        self.get_usd_rates = get_usd_rates
        self.opportunity_interval = opportunity_interval

    async def get_opportunities(self, price_markets=None, close=True, ):
        """
        :param price_markets: Optional. If you would like to first return the prices for the markets in price_markets
        and the corresponding opportunities before finding other opportunities.
        Example value is ['BTC/USD, BTC/USDT, ETH/USD, ETH/USDT]
        For markets in price_markets, return a 2-tuple of (opportunity, prices). Read docstring of _find_opportunity for
        more information.
        """
        self.adapter.info('Finding inter-exchange opportunities.')

        # If you would like to first return the prices for the markets in price_markets and the corresponding
        # opportunities before finding other opportunities
        if price_markets is not None:
            collections = self.collections
            # First collects the prices for the markets in price_markets
            tasks = []
            for market in price_markets:
                tasks.append(self._find_opportunity(market, self.collections[market], True))
                # todo: add if market in price_markets to _find_opportunity. deleting from collections is bad.
                del collections[market]
            for result in asyncio.as_completed(tasks):
                yield await result
        else:
            collections = self.collections

        tasks = [self._find_opportunity(market_name, exchange_list)
                 for market_name, exchange_list in collections.items()]

        for result in asyncio.as_completed(tasks):
            yield await result

        if close:
            tasks = [e.close() for e in self.exchanges.values()]
            await asyncio.wait(tasks)
        self.adapter.info('Yielded all inter-exchange opportunities.')

    async def _find_opportunity(self, market_name, exchange_list, return_prices=False):
        """
        :param return_prices: If True, returns a two-tuple where the first element is the opportunity dict and the
        second element is a dict keyed by exchange name in exchange_list and valued with the corresponding price of
        market_name. If False, returns the opportunity dict
        """
        self._find_opportunity_calls += 1
        self.opportunity_id += 1
        current_opp_id = self.opportunity_id
        await asyncio.sleep(self.opportunity_interval * self._find_opportunity_calls)
        # Try again in 100 milliseconds if any of the exchanges in exchange_list are currently rate limited.
        for e in exchange_list:
            if e in self.rate_limited_exchanges:
                self.adapter.info('Sleeping asynchronously because exchange was rate limited',
                                  exchange=e, sleeptime=0.1, )
                await asyncio.sleep(0.1)
                return await self._find_opportunity(market_name, exchange_list)

        if return_prices:
            prices = {}

        self.adapter.info('Finding opportunity', opportunity=current_opp_id, market=market_name, )
        opportunity = {
            'highest_bid': {'price': -1, 'exchange': None, 'volume': 0},
            'lowest_ask': {'price': float('Inf'), 'exchange': None, 'volume': 0},
            'ticker': market_name,
            'datetime': datetime.datetime.now(tz=datetime.timezone.utc),
            'id': current_opp_id
        }

        tasks = [self._exchange_fetch_order_book(exchange_name, market_name, current_opp_id)
                 for exchange_name in exchange_list]
        for res in asyncio.as_completed(tasks):
            order_book, exchange_name = await res
            # If the order book's volume was too low or fetch_ticker raised ExchangeError or ExchangeNotAvailable
            if exchange_name is None:
                continue
            # If ticker is None, that means that there was either a RequestTimeout or DDosProtection error.
            if order_book is None:
                self.rate_limited_exchanges.add(exchange_name)
                await asyncio.sleep(0.2)
                # Because of asynchronicity, error.exchange_name may no longer be in self.rate_limited_exchanges
                if exchange_name in self.rate_limited_exchanges:
                    self.rate_limited_exchanges.remove(exchange_name)

                if market_name in self.collections:
                    # self.collections[market_name] instead of exchange_list because an exchange is removed if it
                    # raised ExchangeError, which signals that the exchange no longer supports the specified market
                    return await self._find_opportunity(market_name, self.collections[market_name])
                # edge case: if it was removed because there were only two exchanges for this market and one of them
                # was removed because it no longer supports this market. likely will happen only with very low-volume
                # and exotic markets
                else:
                    return opportunity

            bid = order_book['bids'][0][0]
            ask = order_book['asks'][0][0]

            if return_prices:
                prices[exchange_name] = ask

            if bid > opportunity['highest_bid']['price']:
                opportunity['highest_bid']['price'] = bid
                opportunity['highest_bid']['exchange'] = exchange_name
                opportunity['highest_bid']['volume'] = order_book['bids'][0][1]

            if ask < opportunity['lowest_ask']['price']:
                opportunity['lowest_ask']['price'] = ask
                opportunity['lowest_ask']['exchange'] = exchange_name
                opportunity['lowest_ask']['volume'] = order_book['asks'][0][1]

        self.adapter.info('Found opportunity', opportunity=current_opp_id, market=market_name)
        if return_prices:
            return opportunity, prices
        return opportunity

    async def _exchange_fetch_order_book(self, exchange_name, market_name, current_opp_id):
        """
        Returns a two-tuple structured as (ticker, exchange_name)
        ticker is None if an order book with bids and asks was not returned by fetch_order_book
        exchange_name is None if an unavoidable error was raised or the order book has no bids or no asks
        """
        self.adapter.debug('Fetching ticker', opportunity=current_opp_id,
                           exchange=exchange_name, market=market_name)
        try:
            order_book = await self.exchanges[exchange_name].fetch_order_book(market_name)
        except ccxt.DDoSProtection:
            self.adapter.warning('Rate limited for inter-exchange opportunity',
                                 opportunity=current_opp_id,
                                 exchange=exchange_name,
                                 market=market_name)
            return None, exchange_name
        except ccxt.RequestTimeout:
            self.adapter.warning('Request timeout for inter-exchange opportunity.',
                                 opportunity=current_opp_id,
                                 exchange=exchange_name,
                                 market=market_name)
            return None, exchange_name
        # If the exchange no longer has the specified market
        except ccxt.ExchangeError:
            self.adapter.warning('Fetching ticker raised an ExchangeError.', opportunity=current_opp_id,
                                 exchange=exchange_name, market=market_name)
            self.adapter.info('Removing exchange from market', exchange=exchange_name,
                              market=market_name, opportunity=current_opp_id, )
            self.collections.remove_exchange_from_market(exchange_name, market_name)
            return None, None
        except ccxt.ExchangeNotAvailable:
            self.adapter.warning('Fetching ticker raised an ExchangeNotAvailable error.', opportunity=current_opp_id,
                                 exchange=exchange_name, market=market_name)
            return None, None

        if order_book['bids'] == [] or order_book['asks'] == []:
            self.adapter.debug('No asks or no bids', exchange=exchange_name, market=market_name)
            return None, None

        if self.get_usd_rates:
            cap_currency_index = market_name.find('USD')
            # if self.cap_currency is the quote currency
            if cap_currency_index > 0:
                self._add_to_rates_dict(exchange_name, market_name, order_book['bids'][0][0])

        self.adapter.debug('Fetched ticker', opportunity=current_opp_id, exchange=exchange_name,
                           market=market_name)
        return order_book, exchange_name

    def _add_to_rates_dict(self, exchange_name, market_name, price):
        if exchange_name in self.usd_rates:
            self.usd_rates[exchange_name][market_name] = price
        else:
            self.usd_rates[exchange_name] = {market_name: price}


def get_opportunities_for_collection(exchanges, collections, name=True):
    finder = SuperOpportunityFinder(exchanges, collections, name=name)
    return finder.get_opportunities()


async def get_opportunity_for_market(ticker, exchanges=None, name=True, invocation_id=0):
    file_logger.info('Invocation#{} - Finding lowest ask and highest bid for {}'.format(invocation_id, ticker))
    finder = OpportunityFinder(ticker, exchanges=exchanges, name=name)
    result = await finder.find_min_max()
    file_logger.info('Invocation#{} - Found lowest ask and highest bid for {}'.format(invocation_id, ticker))
    return result
