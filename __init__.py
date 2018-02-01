from async_find_opportunities import OpportunityFinder, get_exchange_pairs_for_market
from async_build_markets import build_all_collections, build_specific_collections, CollectionBuilder, \
    SpecificCollectionBuilder


def get_opportunity_for_market(ticker, exchange_list=None):
    finder = OpportunityFinder(ticker, exchange_list)
    return finder.find_min_max()
