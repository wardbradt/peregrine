import tweepy, time
from peregrinearb import get_opportunity_for_market, create_weighted_multi_exchange_digraph, bellman_ford_multi, \
    print_profit_opportunity_for_path_multi
import asyncio
import heapq

# A bot which tweets out the top 3 price disparities from a given set of markets and exchanges.


CONSUMER_KEY = '*'
CONSUMER_SECRET = '*'
ACCESS_KEY = '*'
ACCESS_SECRET = '*'
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

markets = ["ETH/BTC", "BTC/USD", "DASH/BTC", "LTC/BTC", "XRP/BTC"]
market_iterator = 0
exchanges = ['kraken', 'bittrex', 'binance', 'gdax', 'bitstamp', 'gemini']
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
        output += "{}. {}: {} on {} and {} on {}. Disparity: {}%\n".format(i + 1, results[0][2],
                                                                           opportunity['highest_bid']['price'],
                                                                           opportunity['highest_bid']['exchange'].id,
                                                                           opportunity['lowest_ask']['price'],
                                                                           opportunity['lowest_ask']['exchange'].id,
                                                                           str((results[0][0] - 1) * 100))
        if i == 2:
            break
        heapq.heappop(results)
    results = []
    api.update_status(output)

    # does not currently work. comment out all code after this line to use bot in its current working form.

    graph = create_weighted_multi_exchange_digraph(exchanges, log=True)
    graph, paths = bellman_ford_multi(graph, markets[market_iterator].split('/')[0], loop_from_source=True, unique_paths=True)
    for path in paths:
        output = print_profit_opportunity_for_path_multi(graph, path, print_output=False, round_to=2, shorten=True)
        print(output)
        api.update_status(output)
    print('ho')
    market_iterator += 1
    if market_iterator == len(markets):
        market_iterator = 0

    time.sleep(600)  # 10 minutes
