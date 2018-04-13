# This code is modified from examples/test_build_collections.py
from peregrinearb.async_build_markets import build_specific_collections


# This is a dict of the collections only containing exchanges which have the fetch_order_book, create_market_buy_order,
# create_market_sell_order, create_limit_buy_order, and create_limit_sell_order functions.
specific_collections = build_specific_collections(has={'fetchOrderBook': True, 'createOrder': True})
