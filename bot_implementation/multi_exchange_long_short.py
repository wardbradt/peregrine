from peregrinearb import get_opportunity_for_market


async def trade(exchanges: list, market_name, amount):
    """
    When there is a price disparity for a cryptocurrency market on two separate exchanges, buys the currency on the
    exchange with the lowest asking price and short sells on the exchange with the highest bid price. This ensures
    market neutrality and profit when (or if) the similar markets converge.
    todo: implement program to cover short and sell the long upon convergence.

    :param exchanges: A list of ccxt exchange objects. They must be preloaded with the necessary data to allow trading
    (e.g. API keys). Each exchange must allow margin trading.
    :param market_name: A market that is common amongst these exchanges. You can find the exchanges for each market
    at peregrinearb/collections/collections.json
    :param amount: The amount of quote currency in market_name you would like to trade.
    """
    opportunity = await get_opportunity_for_market(market_name, exchanges=exchanges, name=False)

    scalar = opportunity['lowest_ask']['price'] / opportunity['highest_bid']['price']

    await opportunity['lowest_ask']['exchange'].create_order(market_name, 'limit', 'buy', amount,
                                                             opportunity['lowest_ask']['price'])
    await opportunity['highest_bid']['exchange'].create_order(market_name, 'limit',
                                                              'sell', amount * scalar,
                                                              opportunity['highest_bid']['price'],
                                                              {'type': 'market'})


async def cover_positions(market_name, exchange_bought, amount_bought, exchange_sold, amount_sold, price, *args):
    """
    To be called when the user would like to exit the trade (ideally when the prices on exchange_bought and
    exchange_sold have converged).
    :param price: The rate of market_name on exchange_bought.
    :param args: Only one optional positional argument is allowed. It should be the rate of market_name on
    exchange_sold. If no optional positional arguments are given, the rate of market_name on exchange_sold is assumed
    to be price.
    """
    args = list(args)
    if len(args) > 0 and len(args) > 1:
        raise ValueError("Too many arguments given.")
    # if len(args) == 0:
    else:
        args[0] = price

    await exchange_bought.create_order(market_name, 'limit', 'sell', amount_bought, price)
    await exchange_sold.create_order(market_name, 'limit', 'buy', amount_sold, args[0], {'type': 'market'})
