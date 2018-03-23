import json
import math
import networkx as nx
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
    # todo: fix paths to collections
    with open('./../peregrine/collections/collections.json') as f:
        collections = json.load(f)
    for market_name, exchanges in collections.items():
        if market_name == market_ticker:
            return exchanges

    with open('./../peregrine//collections/singularly_available_markets.json') as f:
        singularly_available_markets = json.load(f)
    for market_name, exchange in singularly_available_markets:
        if market_name == market_ticker:
            return [exchange]

    raise ExchangeNotInCollectionsError(market_ticker)


def print_profit_opportunity_for_path(graph, path, round_to=None):
    if not path:
        return

    money = 100
    print("Starting with %(money)i in %(currency)s" % {"money": money, "currency": path[0]})

    for i in range(len(path)):
        if i + 1 < len(path):
            start = path[i]
            end = path[i + 1]
            # todo: rate should not have to be inversed
            rate = math.exp(-graph[start][end]['weight'])
            money *= rate
            if round_to is None:
                print("%(start)s to %(end)s at %(rate)f = %(money)f" % {"start": start, "end": end, "rate": rate,
                                                                        "money": money})
            else:
                print("%(start)s to %(end)s at %(rate)f = %(money)f" % {"start": start, "end": end,
                                                                        "rate": round(rate, round_to),
                                                                        "money": round(money, round_to)})


def print_profit_opportunity_for_path_multi(graph: nx.Graph, path, print_output=True, round_to=None, shorten=False):
    """
    The only difference between this function and the function in utils/general.py is that the print statement
    specifies the exchange name. It assumes all edges in graph and in path have exchange_name and market_name
    attributes.
    """
    if not path:
        return

    money = 100
    result = ''
    result += "Starting with %(money)i in %(currency)s\n" % {"money": money, "currency": path[0]}

    for i in range(len(path)):
        if i + 1 < len(path):
            start = path[i]
            end = path[i + 1]
            rate = math.exp(-graph[start][end]['weight'])
            money *= rate
            if round_to is None:
                result += "{} to {} at {} = {}".format(start, end, rate, money)
            else:
                result += "{} to {} at {} = {}".format(start, end, round(rate, round_to), round(money, round_to))
            if not shorten:
                result += " on {} for {}".format(graph[start][end]['exchange_name'], graph[start][end]['market_name'])

            result += '\n'

    if print_output:
        print(result)
    return result
