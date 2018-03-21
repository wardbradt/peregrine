from peregrine import get_opportunity_for_market
import asyncio


async def trade(exchanges: list, market_name, amount):
    """
    When there is a price disparity for a cryptocurrency market on two separate exchanges, buys the currency on the
    exchange with the lowest asking price and short sells on the exchange with the highest bid price. This ensures
    market neutrality and profit when (or if) the similar markets converge.
    todo: implement program to cover short and sell the long upon convergence.

    :param exchanges: A list of ccxt exchange objects. Each of these exchanges must allow margin trading.
    :param market_name: A market that is common amongst these exchanges. You can find the exchanges for each market
    at peregrine/collections/collections.json
    :param amount: The amount of quote currency in market_name you would like to trade.
    """
    opportunity = get_opportunity_for_market(market_name, exchanges=exchanges, name=False)
    loop = asyncio.get_event_loop()

    scalar = opportunity['lowest_ask']['amount'] / opportunity['highest_bid']['amount']

    futures = [opportunity['lowest_ask']['exchange'].create_order(market_name, 'limit',
                                                                  'buy', amount, opportunity['lowest_ask']['amount']),
               opportunity['highest_bid']['exchange'].create_order(market_name, 'limit',
                                                                   'sell', amount * scalar,
                                                                   opportunity['highest_bid']['amount'],
                                                                   {'type': 'market'})]
    loop.run_until_complete(asyncio.gather(*futures))
