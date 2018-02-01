import ccxt.async as ccxt
import asyncio
import json


class CollectionBuilder:

    def __init__(self):
        all_exchanges = ccxt.exchanges
        # bter frequently has a broken API and flowbtc and yunbi always throw request timeouts.
        [all_exchanges.remove(exchange_name) for exchange_name in ['bter', 'flowbtc', 'yunbi']]
        self.exchanges = all_exchanges
        # keys are market names and values are an array of names of exchanges which support that market
        self.collections = {}
        # stores markets which are only available on one exchange: keys are markets names and values are exchange names
        self.singularly_available_markets = {}

    def build_all_collections(self, write=True):
        futures = [asyncio.ensure_future(self._add_exchange_to_collections(exchange_name)) for exchange_name in
                   self.exchanges]
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*futures))

        if write:
            with open('collections.json', 'w') as outfile:
                json.dump(self.collections, outfile)

            with open('singularly_available_markets.json', 'w') as outfile:
                json.dump(self.singularly_available_markets, outfile)

        return self.collections

    async def _add_exchange_to_collections(self, exchange_name):
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
    async def _get_exchange(exchange_name):
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
        except ccxt.BaseError:
            print("{} threw an error".format(exchange_name))
            return None

        return exchange


class SpecificCollectionBuilder(CollectionBuilder):

    def __init__(self, rules, blacklist=False):
        super().__init__()
        self.blacklist = blacklist
        self.rules = rules

    async def _add_exchange_to_collections(self, exchange_name):
        exchange = await self._get_exchange(exchange_name)
        if exchange is None:
            return

        for key, desired_value in self.rules.items():
            if exchange[key]:
                exchange_value = exchange[key]
            else:
                raise ValueError("{} is not a valid property of {}".format(key, exchange.name))
            if isinstance(exchange_value, str):
                # Note, this line is A XOR B where A is self.blacklist and B is exchange_value != desired_value
                if self.blacklist != (exchange_value != desired_value):
                    return
            elif isinstance(exchange_value, list):
                # The comment above the previous conditional also explains this conditional
                if self.blacklist != (desired_value not in exchange_value):
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


def build_all_collections(write=True):
    builder = CollectionBuilder()
    return builder.build_all_collections(write)


def build_specific_collections(rules, blacklist=False, write=False):
    builder = SpecificCollectionBuilder(rules, blacklist)
    return builder.build_all_collections(write)
