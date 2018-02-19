import json
import math

from ccxt import async as ccxt


class ExchangeNotInCollectionsError(Exception):
    def __init__(self, market_ticker):
        super(ExchangeNotInCollectionsError, self).__init__("{} is either an invalid exchange or has a broken API."
                                                            .format(market_ticker))


async def _get_exchange(exchange_name: str):
    exchange = getattr(ccxt, exchange_name)()
    await exchange.load_markets()
    return exchange


def get_exchanges_for_market(market_ticker):
    """
    Returns the list of exchanges on which a market is traded
    """
    with open('collections/collections.json') as f:
        collections = json.load(f)
    for market_name, exchanges in collections.items():
        if market_name == market_ticker:
            return exchanges

    with open('collections/singularly_available_markets.json') as f:
        singularly_available_markets = json.load(f)
    for market_name, exchange in singularly_available_markets:
        if market_name == market_ticker:
            return [exchange]

    raise ExchangeNotInCollectionsError(market_ticker)


def print_profit_opportunity_for_path(graph, path):
    money = 100
    print("Starting with %(money)i in %(currency)s" % {"money": money, "currency": path[0]})

    for i in range(len(path)):
        if i + 1 < len(path):
            start = path[i]
            end = path[i + 1]
            # todo: rate should not have to be inversed
            rate = math.exp(-graph[start][end]['weight'])
            money *= rate
            print("%(start)s to %(end)s at %(rate)f = %(money)f" % {"start": start, "end": end, "rate": rate,
                                                                    "money": money})