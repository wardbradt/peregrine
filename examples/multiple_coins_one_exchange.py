import asyncio
from peregrine import load_exchange_graph, print_profit_opportunity_for_path
from bellmannx import NegativeWeightFinder


loop = asyncio.get_event_loop()
graph = loop.run_until_complete(load_exchange_graph('bittrex'))

paths = NegativeWeightFinder(graph).bellman_ford('BTC')
for path in paths:
    print_profit_opportunity_for_path(graph, path)
