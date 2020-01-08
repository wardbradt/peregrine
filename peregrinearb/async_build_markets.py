import ccxt.async_support as ccxt
import asyncio
import json
from .utils.general import ExchangeNotInCollectionsError
from .settings import COLLECTIONS_DIR

__all__ = [
    'CollectionBuilder',
    'SymbolCollectionBuilder',
    'SpecificCollectionBuilder',
    'get_exchanges_for_market',
    'build_specific_collections',
    'build_collections',
]


class CollectionBuilder:

    def __init__(self, exchanges=None):
        if exchanges is None:
            exchanges = ccxt.exchanges
        self.exchanges = exchanges
        # keys are market names and values are an array of names of exchanges which support that market
        self.collections = {}
        # stores markets which are only available on one exchange: keys are markets names and values are exchange names
        self.singularly_available_markets = {}

    async def build_collections(self, write=True, ccxt_errors=True, ):
        """
        Refer to glossary.md for the definition of a "collection"
        :param write: If true, will write collections and singularly_available_markets to json files in /collections
        :param ccxt_errors: If true, this method will raise the errors ccxt raises
        :return: A dictionary where keys are market names and values are lists of exchanges which support the respective
        market name
        """
        tasks = [self._add_exchange_to_collections(exchange, ccxt_errors, ) for exchange
                 in self.exchanges]
        await asyncio.wait(tasks)

        if write:
            with open(COLLECTIONS_DIR + 'collections.json', 'w') as outfile:
                json.dump(self.collections, outfile)

            with open(COLLECTIONS_DIR + 'singularly_available_markets.json', 'w') as outfile:
                json.dump(self.singularly_available_markets, outfile)

        return self.collections

    async def _add_exchange_to_collections(self, exchange_name: str, ccxt_errors=False, ):
        exchange = getattr(ccxt, exchange_name)()
        try:
            await exchange.load_markets()
            await exchange.close()
        except ccxt.BaseError as e:
            if ccxt_errors:
                await exchange.close()
                raise e
            return

        for symbol in exchange.symbols:
            if symbol in self.collections:
                self.collections[symbol].append(exchange_name)
            elif symbol in self.singularly_available_markets:
                self.collections[symbol] = [self.singularly_available_markets[symbol], exchange_name]
                del self.singularly_available_markets[symbol]
            else:
                self.singularly_available_markets[symbol] = exchange_name


class SymbolCollectionBuilder(CollectionBuilder):

    def __init__(self, exchanges: list = None, symbols: list = None, exclusive_currencies: list = None,
                 inclusive_currencies: list = None):
        """
        :param symbols: symbols which should be added to the collections
        :param exclusive_currencies: currencies for which markets should be fetched if the paired currency is also
        in exclusive_currencies
        :param inclusive_currencies: currencies for which all markets should be fetched
        """
        if exchanges is None:
            exchanges = []
        if symbols is None:
            symbols = []
        if exclusive_currencies is None:
            exclusive_currencies = []
        if inclusive_currencies is None:
            inclusive_currencies = []
        super(SymbolCollectionBuilder, self).__init__(exchanges)
        self.symbols = symbols
        self.exclusive_currencies = exclusive_currencies
        self.inclusive_currencies = inclusive_currencies

    async def _add_exchange_to_collections(self, exchange: ccxt.Exchange, ccxt_errors=True, ):
        try:
            await exchange.load_markets()
        except ccxt.BaseError as e:
            if ccxt_errors:
                await exchange.close()
                raise e
            return

        exch_currencies = exchange.currencies
        for i, i_currency in enumerate(self.exclusive_currencies):
            if i_currency not in exch_currencies:
                continue
            for j in range(i + 1, len(self.exclusive_currencies)):
                if self.exclusive_currencies[j] not in exch_currencies:
                    continue
                symbol = '{}/{}'.format(i_currency, self.exclusive_currencies[j])
                if symbol in exchange.symbols:
                    self._add_exchange_to_symbol(symbol, exchange.id)
                else:
                    symbol = '{}/{}'.format(self.exclusive_currencies[j], i_currency)
                    if symbol in exchange.symbols:
                        self._add_exchange_to_symbol(symbol, exchange.id)

        for symbol in exchange.symbols:
            try:
                base, quote = symbol.split('/')
            # for spot and other weird markets
            except ValueError:
                continue
            if base in self.inclusive_currencies or quote in self.inclusive_currencies:
                self._add_exchange_to_symbol(symbol, exchange.id)
            # elif because it was already added
            elif symbol in self.symbols:
                self._add_exchange_to_symbol(symbol, exchange.id)

    def _add_exchange_to_symbol(self, key, value):
        if key not in self.collections:
            self.collections[key] = [value]
        else:
            if value not in self.collections[key]:
                self.collections[key].append(value)


class SpecificCollectionBuilder(CollectionBuilder):

    def __init__(self, blacklist=False, **kwargs):
        """
        **kwargs should restrict acceptable exchanges. Only acceptable keys and values are strings. Look at this part of
        the ccxt manual: https://github.com/ccxt/ccxt/wiki/Manual#user-content-exchange-structure for insight into what
        are acceptable rules.

        When a value in kwargs is a list x, SpecificCollectionBuilder builds a collection of exchanges in which
        the property (designated by the key corresponding to x) contains all elements in x.

        When a value in kwargs is a dict x, SpecificCollectionBuilder builds a collection of exchanges in which the
        specified property (designated by the key corresponding to x) is a dict and contains all key/ value pairs in x.

        Typical use case for **kwargs is 'countries' as a key and Australia, Bulgaria, Brazil, British Virgin
        Islands, Canada, China, Czech Republic, EU, Germany, Hong Kong, Iceland, India, Indonesia, Israel, Japan,
        Mexico, New Zealand, Panama, Philippines, Poland, Russia, Seychelles, Singapore, South Korea,
        St. Vincent & Grenadines, Sweden, Tanzania, Thailand, Turkey, US, UK, Ukraine, or Vietnam as a value.
        """
        super().__init__()
        self.rules = kwargs
        self.blacklist = blacklist

    async def _add_exchange_to_collections(self, exchange_name: str, ccxt_errors=True, name=True):
        if name:
            exchange = getattr(ccxt, exchange_name)()
        if ccxt_errors:
            await exchange.load_markets()
            await exchange.close()
        else:
            try:
                await exchange.load_markets()
                await exchange.close()
            except ccxt.BaseError:
                await exchange.close()
                return

        # Implicitly (and intentionally) does not except ValueErrors raised by _check_exchange_meets_criteria
        if self._check_exchange_meets_criteria(exchange):
            # Having reached this, it is known that exchange meets the criteria given in **kwargs.
            for market_name in exchange.symbols:
                if market_name in self.collections:
                    self.collections[market_name].append(exchange_name)
                elif market_name in self.singularly_available_markets:
                    self.collections[market_name] = [self.singularly_available_markets[market_name], exchange_name]
                    del self.singularly_available_markets[market_name]
                else:
                    self.singularly_available_markets[market_name] = exchange_name

    def _check_exchange_meets_criteria(self, exchange):
        for key, desired_value in self.rules.items():
            try:
                actual_value = getattr(exchange, key)
            except AttributeError:
                raise ValueError("{} is not a valid property of {}".format(key, exchange.name))

            if isinstance(actual_value, list):
                # in all cases where an attribute of an exchange is a list, that list's elements' types are uniform
                # so type of the first element == type of all elements
                type_of_actual_value = type(actual_value[0])
                # this will not work for any Exchange property which is a list of lists (there currently are no such
                # properties)
                if isinstance(desired_value, list):
                    for element in desired_value:
                        if not self._element_of_type_in_list(element, type_of_actual_value, actual_value, key):
                            return False
                else:
                    return self._element_of_type_in_list(desired_value, type_of_actual_value, actual_value, key)

            elif isinstance(actual_value, dict):
                # When given a dict as a desired value, this checks that the values in the actual value are equal to
                # the values in desired value
                if not isinstance(desired_value, dict):
                    raise ValueError("Exchange attribute {} is a dict but supplied preferred value {} is not a dict"
                                     .format(key, desired_value))
                desired_value_items = desired_value.items()
                for key_a, value_a in desired_value_items:
                    # this line is A XOR B where A is self.blacklist and B is desired_value not in actual_value
                    if self.blacklist != (actual_value[key_a] != value_a):
                        return False
            else:
                # if desired_value is a list of length 1 and its only element == actual_value (or != if self.blacklist)
                if isinstance(desired_value, list):
                    if len(desired_value) == 1 and (self.blacklist != (actual_value != desired_value[0])):
                        return False
                elif self.blacklist != (actual_value != desired_value):
                    return False
        return True

    def _element_of_type_in_list(self, element, actual_value_type, actual_value, key):
        """
        :param actual_value: A list
        :param actual_value_type: Type of all elements in actual_value
        :param key: The name of the Exchange property
        :return: a boolean
        """

        if not isinstance(element, actual_value_type):
            raise ValueError("Exchange attribute {} is a list of {}s. "
                             "A non-{} object was passed.".format(key, str(actual_value_type),
                                                                  str(actual_value_type)))
        return self.blacklist == (element not in actual_value)


async def build_specific_collections(blacklist=False, write=False, ccxt_errors=False, **kwargs):
    builder = SpecificCollectionBuilder(blacklist, **kwargs)
    return await builder.build_collections(write, ccxt_errors)


async def build_collections(exchanges=None, write=True, ccxt_errors=False):
    return await CollectionBuilder(exchanges).build_collections(write, ccxt_errors)


async def get_exchanges_for_market(symbol, collections_dir='./'):
    """
    Returns the list of exchanges on which a market is traded
    """
    try:
        with open('{}collections.json'.format(collections_dir)) as f:
            collections = json.load(f)
        for market_name, exchanges in collections.items():
            if market_name == symbol:
                return exchanges
    except FileNotFoundError:
        return await build_specific_collections(symbols=[symbol])

    with open('{}singularly_available_markets.json'.format(collections_dir)) as f:
        singularly_available_markets = json.load(f)
    for market_name, exchange in singularly_available_markets:
        if market_name == symbol:
            return [exchange]

    raise ExchangeNotInCollectionsError(symbol)
