import asyncio
from utils.single_exchange import load_exchange_graph
from utils.general import print_profit_opportunity_for_path
from bellmannx import NegativeWeightFinder


loop = asyncio.get_event_loop()
graph = loop.run_until_complete(load_exchange_graph('bittrex'))

path = NegativeWeightFinder(graph).bellman_ford('BTC')
print_profit_opportunity_for_path(graph, path)
