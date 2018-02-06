from peregrine.async_find_opportunities import OpportunityFinder
from peregrine.async_build_markets import build_collections, build_all_collections, build_specific_collections, \
    CollectionBuilder, SpecificCollectionBuilder
from peregrine.utils import SingularlyAvailableExchangeError, InvalidExchangeError, get_exchange_pairs_for_market


def get_opportunity_for_market(ticker, exchange_list=None):
    finder = OpportunityFinder(ticker, exchange_list)
    return finder.find_min_max()
