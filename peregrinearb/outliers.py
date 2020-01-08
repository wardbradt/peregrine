import ccxt.async_support as ccxt
import asyncio
import time
import numpy as np
from .async_build_markets import get_exchanges_for_market


class OutlierDetector:
    def __init__(self):
        self.request_time_dict = {}

    async def load_markets_for_exchange(self, exchange_name):
        start_time = time.time()
        exchange = getattr(ccxt, exchange_name)()
        try:
            await exchange.load_markets()
        except ccxt.AuthenticationError:
            return None
        except ccxt.RequestTimeout:
            print("request timeout: " + str(exchange_name) + " in " + str(time.time() - start_time) + " seconds")
            return None
        except ccxt.ExchangeNotAvailable:
            return None
        except ccxt.BaseError as e:
            return None
        duration = time.time() - start_time

        self.request_time_dict[exchange_name] = duration


def clean_request_timeout_for_market(market_name):
    return clean_request_timeout_for_exchanges(get_exchanges_for_market(market_name))


def clean_request_timeout_for_exchanges(exchange_list):
    detector = OutlierDetector()
    futures = [asyncio.ensure_future(detector.load_markets_for_exchange(exchange_name)) for exchange_name in
               exchange_list]
    asyncio.get_event_loop().run_until_complete(asyncio.gather(*futures))
    return detector.request_time_dict


async def get_request_times(exchange_list):
    detector = OutlierDetector()
    futures = [asyncio.ensure_future(detector.load_markets_for_exchange(exchange_name)) for exchange_name in
               exchange_list]
    await asyncio.get_event_loop().run_until_complete(asyncio.gather(*futures))
    return detector.request_time_dict


def reject_outliers(data: dict, m=2):
    """
    Modified from a function found at
    https://stackoverflow.com/questions/11686720/is-there-a-numpy-builtin-to-reject-outliers-from-a-list to reject
    outliers above m * standard deviation instead of above and below.
    :param data:
    :param m:
    :return:
    """
    values = list(data.values())
    mean = np.mean(values)
    std = np.std(values)
    filtered = [exchange_name for exchange_name, request_time in data.items() if (request_time < mean + m * std)]
    return filtered
