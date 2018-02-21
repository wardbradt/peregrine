from peregrine import create_weighted_multi_exchange_digraph, bellman_ford_multi, print_profit_opportunity_for_path_multi


graph = create_weighted_multi_exchange_digraph(['kraken', 'bittrex', 'gemini'], log=True)
path = bellman_ford_multi(graph, 'ETH')
print_profit_opportunity_for_path_multi(graph, path)
