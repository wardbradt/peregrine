import json


class SingularlyAvailableExchangeError(Exception):
    def __init__(self, market_ticker):
        super(SingularlyAvailableExchangeError, self).__init__("{} is available on only one exchange."
                                                               .format(market_ticker))


class ExchangeNotInCollectionsError(Exception):
    def __init__(self, market_ticker):
        super(ExchangeNotInCollectionsError, self).__init__("{} is either an invalid exchange or has a broken API."
                                                            .format(market_ticker))


def get_exchange_pairs_for_market(market_ticker):

    with open('collections/collections.json') as f:
        collections = json.load(f)
    for market_name, exchanges in collections.items():
        if market_name == market_ticker:
            return exchanges

    with open('collections/singularly_available_markets.json') as f:
        singularly_available_markets = json.load(f)
    for market_name, exchange in singularly_available_markets:
        if market_name == market_ticker:
            raise SingularlyAvailableExchangeError(market_ticker)

    raise ExchangeNotInCollectionsError(market_ticker)
