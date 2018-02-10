import ccxt.async as ccxt
import asyncio
import json


class CollectionBuilder:

    def __init__(self):
        all_exchanges = ccxt.exchanges
        # bter frequently has a broken API and flowbtc and yunbi always throw request timeouts.
        # [all_exchanges.remove(exchange_name) if exchange_name in all_exchanges else None for exchange_name in
        # ['bter', 'flowbtc', 'yunbi']]
        self.exchanges = all_exchanges
        # keys are market names and values are an array of names of exchanges which support that market
        self.collections = {}
        # stores markets which are only available on one exchange: keys are markets names and values are exchange names
        self.singularly_available_markets = {}

    def build_all_collections(self, write=True, ccxt_errors=False):
        """
        Refer to glossary.md for the definition of a "collection"
        :param write: If true, will write collections and singularly_available_markets to json files in /collections
        :param ccxt_errors: If true, this method will raise the errors ccxt raises
        :return:
        """
        futures = [asyncio.ensure_future(self._add_exchange_to_collections(exchange_name, ccxt_errors)) for
                   exchange_name in self.exchanges]
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*futures))

        if write:
            with open('collections/collections.json', 'w') as outfile:
                json.dump(self.collections, outfile)

            with open('collections/singularly_available_markets.json', 'w') as outfile:
                json.dump(self.singularly_available_markets, outfile)

        return self.collections

    async def _add_exchange_to_collections(self, exchange_name: str, ccxt_errors=False):
        exchange = await _get_exchange(exchange_name, ccxt_errors)
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


async def _get_exchange(exchange_name: str, ccxt_errors=False):
    """
    :param ccxt_errors: if true, raises errors ccxt raises when calling load_markets. The common ones are
    RequestTimeout and ExchangeNotAvailable, which are caused by problems with exchanges' APIs.
    """
    exchange = getattr(ccxt, exchange_name)()

    if ccxt_errors:
        await exchange.load_markets
    else:
        try:
            await exchange.load_markets()
        except ccxt.BaseError:
            return None

    return exchange


class ExchangeFailsCriteriaError(Exception):
    pass


class SpecificCollectionBuilder(CollectionBuilder):

    def __init__(self, blacklist=False, **kwargs):
        """
        **kwargs should restrict acceptable exchanges. Only acceptable keys and values are strings. Look at this part of
        the ccxt manual: https://github.com/ccxt/ccxt/wiki/Manual#user-content-exchange-structure for insight into what
        are acceptable rules.

        Typical use case for **kwargs is 'countries' as a key and Australia, Bulgaria, Brazil, British Virgin
        Islands, Canada, China, Czech Republic, EU, Germany, Hong Kong, Iceland, India, Indonesia, Israel, Japan,
        Mexico, New Zealand, Panama, Philippines, Poland, Russia, Seychelles, Singapore, South Korea,
        St. Vincent & Grenadines, Sweden, Tanzania, Thailand, Turkey, US, UK, Ukraine, or Vietnam as a value.
        """
        super().__init__()
        self.rules = kwargs
        self.blacklist = blacklist

    def check_exchange_meets_criteria(self, exchange):

        for key, desired_value in self.rules.items():
            try:
                actual_value = getattr(exchange, key)
            except AttributeError:
                raise ValueError("{} is not a valid property of {}".format(key, exchange.name))

            if isinstance(actual_value, list):
                # in all cases where an attribute of an exchange is a list, that list's elements' types are uniform
                # so type of the first element is representative of type of all elements
                type_of_actual_value = type(actual_value[0])
                if not isinstance(desired_value, type_of_actual_value):
                    raise ValueError("Exchange attribute {} is a list of {}s. "
                                     "A non-{} object was passed.".format(key, str(type_of_actual_value),
                                                                          str(type_of_actual_value)))
                # Note, this line is A XOR B where A is self.blacklist and B is desired_value not in actual_value
                if self.blacklist != (desired_value not in actual_value):
                    raise ExchangeFailsCriteriaError()
            elif isinstance(actual_value, dict):
                # When given a dict as a desired value, this checks that the values in the actual value are equal to
                # the values in desired value
                if not isinstance(desired_value, dict):
                    raise ValueError("Exchange attribute {} is a dict but supplied preferred value {} is not a dict"
                                     .format(key, desired_value))
                desired_value_items = desired_value.items()
                for key_a, value_a in desired_value_items:
                    if self.blacklist != (actual_value[key_a] != value_a):
                        raise ExchangeFailsCriteriaError()

            else:
                if self.blacklist != (actual_value != desired_value):
                    raise ExchangeFailsCriteriaError()

    async def _add_exchange_to_collections(self, exchange_name: str, ccxt_errors=False):
        exchange = await _get_exchange(exchange_name, ccxt_errors)
        if exchange is None:
            return

        # Implicitly (and intentionally) does not except ValueErrors raised by check_exchange_meets_criteria
        try:
            self.check_exchange_meets_criteria(exchange)
        except ExchangeFailsCriteriaError:
            return

        # Having reached this, it is known that exchange meets the criteria given in **kwargs.
        for market_name in exchange.symbols:
            if market_name in self.collections:
                self.collections[market_name].append(exchange_name)
            elif market_name in self.singularly_available_markets:
                self.collections[market_name] = [self.singularly_available_markets[market_name], exchange_name]
                del self.singularly_available_markets[market_name]
            else:
                self.singularly_available_markets[market_name] = exchange_name


class ExchangeCurrencyBuilder:

    def __init__(self, symbol):
        """
        THIS CLASS IS CURRENTLY IN DEVELOPMENT. IT DOES NOT WORK.

        self.graph is a a dict representing a graph. Each key is a currency base symbol c representing a graph
        node. Each node has at least two edges. The node(s) which share(s) these edges must also have at least two
        edges. This is because a node which connects to only   Each value is a dict d. In d, every key represents a quote currency q for c. each value of q in d is a
        dict f. in f, each key is an exchange and each value is the name of the market (either c/q or q/c). The
        following is a visualization of self.collections:

        {base_currency:
            {quote_currency_a:
                {exchange_one: base_currency/quote_currency_a, exchange_two: quote_currency_a/base_currency}
            }
            {quote_currency_b:
                {exchange_one: quote_currency_b/base_currency, exchange_three: base_currency/quote_currency_b}
            }
            {quote_currency_c:
                {exchange_four: quote_currency_c/base_currency, exchange_two: base_currency/quote_currency_c}
            }
        }

        self.singularly_available_currencies (sac) is a dict. in it, each key is a currency which has been found on
        only one market across all exchanges and thus cannot be arbitraged. each value is a dict with two elements
        'exchange' and 'market'. an example key/value pair in sac would look like:

        'USD': {'exchange_name': 'bittrex', 'market_name': 'BTC/USD'}

        This example would occur when USD has only been encountered once.

        :param symbol: A currency symbol (e.g. USD, BTC, XRP)
        """
        self.symbol = symbol
        self.exchanges = ccxt.exchanges
        self.graph = {}
        self.singularly_available_currencies = {}

    def build_all_collections(self, write=False, ccxt_errors=False):
        futures = [asyncio.ensure_future(self._add_exchange_to_collections(exchange_name, ccxt_errors)) for
                   exchange_name in self.exchanges]
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*futures))

        if write:
            with open('collections/graph.json', 'w') as outfile:
                json.dump(self.graph, outfile)

            with open('collections/singularly_available_currencies.json', 'w') as outfile:
                json.dump(self.singularly_available_currencies, outfile)

        return self.graph

    def add_sac(self, currency, exchange_name, market_name):
        self.singularly_available_currencies[currency] = {}
        self.singularly_available_currencies[currency]['exchange_name'] = exchange_name
        self.singularly_available_currencies[currency]['market_name'] = market_name

    async def _add_exchange_to_collections(self, exchange_name: str, ccxt_errors=False):
        """
        Never connect to a node that does not exist. If a cryptocurrency is available on only one market on one
        exchange, it should not be added to graph.

        THIS METHOD DOES NOT CURRENTLY WORK. IT, ALONG WITH THE REST OF THE CLASS, IS IN DEVELOPMENT.
        """
        exchange = await _get_exchange(exchange_name, ccxt_errors)
        if exchange is None:
            return

        quote_currency_in_graph = None
        for market_name in exchange.symbols:
            base_currency, quote_currency = market_name.split("/")

            # if base_currency or quote_currency have not yet been encountered, add the un-encountered to
            # self.singularly_available_currencies and ignore this market
            if base_currency not in self.graph:
                # if base_currency has been encountered before
                if base_currency in self.singularly_available_currencies:
                    # if quote_currency not in self.graph, do nothing because it is a sac and nodes for SACs should not
                    # be added to the graph
                    if quote_currency not in self.graph:
                        self.add_sac(quote_currency, exchange_name, market_name)
                        continue
                    else:
                        # it is known that quote_currency in self.graph. set quote_currency_in_graph = True so it
                        # doesn't have to be called later.
                        quote_currency_in_graph = True
                        # else, add base_currency to self.graph and remove from self.singularly_available_currencies
                        self.graph[base_currency] = {}
                        self.graph[base_currency][quote_currency] = {exchange_name: market_name}

                        popped_base = self.singularly_available_currencies.pop(base_currency)

                        # the quote currency from the first time base currency was encountered
                        # todo: does this modify popped_base['market_name']? if so, this will cause errors.
                        popped_base_quote = popped_base['market_name'].replace(base_currency, '').strip('/')

                        # edge case: if the first time base_currency was encountered it was against quote_currency
                        if popped_base_quote == quote_currency:
                            self.graph[base_currency][quote_currency][popped_base['exchange_name']] = market_name
                        # else: need to instantiate [base_currency][popped_base_quote] as a dict first
                        else:
                            self.graph[base_currency][popped_base_quote] = {}
                            self.graph[base_currency][popped_base_quote][popped_base['exchange_name']] = \
                                popped_base['market_name']
                # if this is the first time encountering base_currency
                else:

                    pass
            # both quote_currency and base_currency in self.graph
            else:
                if quote_currency in self.graph[base_currency]:
                    self.graph[base_currency][quote_currency][exchange_name] = market_name
                # have not yet encountered a market where base_currency and quote_currency are traded against each
                # other, so ignore this market
                # else:


def get_exchanges_for_currency(symbol):
    """
    DOES NOT WORK YET
    
    Returns a dict where each key is the name of an exchange e which has symbol as the base or quote currency on at
    least one market and each value is the list of markets on e where symbol is a base or quote currency.
    :param symbol: A currency symbol (e.g. USD, BTC, XRP)
    """
    with open('collections/collections.json') as f:
        collections = json.load(f)

    passed_exchanges = []
    # for market_name, exchanges in collections.items():
    #     base, quote = market_name.split('/')
    #     if base == symbol:
    #         pass
    #     elif quote == symbol:
    #
    #     if market_name == market_ticker:
    #         return exchanges


def build_collections(blacklist=False, write=True, ccxt_errors=False):
    return build_specific_collections(blacklist, write,
                                      ccxt_errors, has={'fetchOrderBook': True})


def build_specific_collections(blacklist=False, write=False, ccxt_errors=False, **kwargs):
    builder = SpecificCollectionBuilder(blacklist, **kwargs)
    return builder.build_all_collections(write, ccxt_errors)


def build_all_collections(write=True, ccxt_errors=False):
    """
    Be careful when using this. build_collections is typically preferred over this method because build_collections only
    accounts for exchanges which have a private API (and thus can be traded on).
    :param write:
    :param ccxt_errors:
    :return:
    """
    builder = CollectionBuilder()
    return builder.build_all_collections(write=write, ccxt_errors=ccxt_errors)
