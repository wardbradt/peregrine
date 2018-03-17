import asyncio
from peregrine import load_exchange_graph, print_profit_opportunity_for_path, bellman_ford


loop = asyncio.get_event_loop()
graph = loop.run_until_complete(load_exchange_graph('binance'))

paths = bellman_ford(graph, 'BTC')
for path in paths:
    print_profit_opportunity_for_path(graph, path)
