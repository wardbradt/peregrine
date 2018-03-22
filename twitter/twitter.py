import tweepy, time
from peregrine import get_opportunity_for_market
import asyncio
import heapq

# A bot which tweets out the top 3 price disparities from a given set of markets and exchanges.


CONSUMER_KEY = 'KcvRmdAYfi626A7jZPZTAQFNR'
CONSUMER_SECRET = 'Rb3fRsvp0dskgdW47Pb9ZeDvHNjeiAABMy7gXe5g4BgBCfJDt4'
ACCESS_KEY = '770972975403143170-b41MXpnr3RFDYAaCTi1ie7fI13CJrnk'
ACCESS_SECRET = 'us5eWbMlT2mNEGMoUbUclrfcecqGXb88B5Uyu1AqbjWJo'
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

markets = ["ETH/BTC", "BTC/USD", "DASH/BTC", "LTC/BTC", "XRP/BTC"]
exchanges = ['kraken', 'bittrex', 'binance', 'gdax', 'bitstamp', 'gemini', 'bitfinex']
results = []


async def add_to_result(market, exchanges):
    opportunity = await get_opportunity_for_market(market, exchanges=exchanges)
    ratio = opportunity['highest_bid']['price'] / opportunity['lowest_ask']['price']
    heapq.heappush(results, (ratio, opportunity, market))


while True:
    futures = [asyncio.ensure_future(add_to_result(market, exchanges=exchanges)) for market in markets]
    asyncio.get_event_loop().run_until_complete(asyncio.gather(*futures))

    output = ''
    for i in range(len(markets)):
        opportunity = results[0][1]
        output += "{}. {}: {} on {} and {} on {}. Disparity: {}\n".format(i + 1, results[0][2],
                                                                          opportunity['highest_bid']['price'],
                                                                          opportunity['highest_bid']['exchange'].id,
                                                                          opportunity['lowest_ask']['price'],
                                                                          opportunity['lowest_ask']['exchange'].id,
                                                                          results[0][0])
        if i == 2:
            break
        heapq.heappop(results)

    api.update_status(output)
    time.sleep(600)
    results = []
