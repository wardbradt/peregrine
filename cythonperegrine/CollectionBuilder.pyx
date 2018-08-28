import ccxt.async_support as ccxt
import asyncio
import json


cdef class CollectionBuilder:

    def __init__(self):
        cdef list all_exchanges = ccxt.exchanges
        # bter frequently has a broken API and flowbtc and yunbi always throw request timeouts.
        [all_exchanges.remove(exchange_name) if exchange_name in all_exchanges else None for exchange_name in ['bter', 'flowbtc', 'yunbi']]
        self.exchanges = all_exchanges
        # keys are market names and values are an array of names of exchanges which support that market
        self.collections = {}
        # stores markets which are only available on one exchange: keys are markets names and values are exchange names
        self.singularly_available_markets = {}

    async def _add_exchange_to_collections(self, exchange_name: str):
        exchange = await self._get_exchange(exchange_name)
        if exchange is None:
            return
        for market_name in exchange.symbols:
            if market_name in self.collections:
                self.collections[market_name].append(exchange_name)
            elif market_name in self.singularly_available_markets:
                self.collections[market_name] = [self.singularly_available_markets[market_name], exchange_name]
                del self.singularly_available_markets[market_name]
            else:
                self.singularly_available_markets[market_name] = exchange_name

    @staticmethod
    async def _get_exchange(exchange_name: str):
        exchange = getattr(ccxt, exchange_name)()

        try:
            await exchange.load_markets()
        except ccxt.AuthenticationError:
            return None
        except ccxt.RequestTimeout:
            print("request timeout: " + exchange_name)
            return None
        except ccxt.ExchangeNotAvailable:
            print("not available: " + exchange_name)
            return None
        except ccxt.BaseError as e:
            print("{} threw {}".format(exchange_name, str(e)))
            return None

        return exchange


cdef class SpecificCollectionBuilder(CollectionBuilder):

    def __init__(self, rules, blacklist=False):
        super().__init__()
        self.blacklist = blacklist
        self.rules = rules

    async def _add_exchange_to_collections(self, exchange_name: str):
        exchange = await self._get_exchange(exchange_name)
        if exchange is None:
            return

        for key, desired_value in self.rules.items():
            try:
                actual_value = getattr(exchange, key)
            except AttributeError:
                raise ValueError("{} is not a valid property of {}".format(key, exchange.name))
            if isinstance(actual_value, str):
                # Note, this line is A XOR B where A is self.blacklist and B is actual_value != desired_value
                if self.blacklist != (actual_value != desired_value):
                    return
            elif isinstance(actual_value, list):
                # The comment above the previous conditional also explains this conditional
                if self.blacklist != (desired_value not in actual_value):
                    return
            else:
                raise ValueError("The rules parameter for SpecificCollectionBuilder takes only strings and lists"
                                 "as values.")

        for market_name in exchange.symbols:
            if market_name in self.collections:
                self.collections[market_name].append(exchange_name)
            elif market_name in self.singularly_available_markets:
                self.collections[market_name] = [self.singularly_available_markets[market_name], exchange_name]
                del self.singularly_available_markets[market_name]
            else:
                self.singularly_available_markets[market_name] = exchange_name


cpdef dict build_all_collections(CollectionBuilder builder, bool write):
    """
    
    :param builder: A CollectionBuilder object. Can be None.
    :param write: If collections and singularly_available_markets should be written to the JSON files in the collections
    directory. Must be True or False.
    :return: 
    """
    if builder is None:
        builder = CollectionBuilder()
    cdef list futures = [asyncio.ensure_future(builder._add_exchange_to_collections(exchange_name)) for exchange_name in
                   builder.exchanges]
    asyncio.get_event_loop().run_until_complete(asyncio.gather(*futures))

    if write:
        with open('cythonperegrine/collections/collections.json', 'w') as outfile:
            json.dump(builder.collections, outfile)

        with open('cythonperegrine/collections/singularly_available_markets.json', 'w') as outfile:
            json.dump(builder.singularly_available_markets, outfile)

    return builder.collections


cpdef dict build_specific_collections(dict rules, bool blacklist, bool write):
    """
    :param rules:
    :param blacklist: if true, rules will serve as a blacklist instead of a whitelist.
    :param write: if true, the program will write to the JSON files in collections
    :return: 
    """
    builder = SpecificCollectionBuilder(rules, blacklist)
    return build_all_collections(builder, write)


