from cythonperegrine.CollectionBuilder import build_specific_collections, build_all_collections, \
    SpecificCollectionBuilder
from cythonperegrine.OpportunityFinder import OpportunityFinder, get_exchange_pairs_for_market


def get_opportunity_for_market(ticker, exchange_list=None):
    finder = OpportunityFinder(ticker, exchange_list)
    return finder.find_min_max()
