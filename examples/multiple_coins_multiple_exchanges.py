from peregrinearb import create_weighted_multi_exchange_digraph, bellman_ford_multi, \
    print_profit_opportunity_for_path_multi


graph = create_weighted_multi_exchange_digraph(['bittrex', 'gemini', 'kraken'], log=True)

graph, paths = bellman_ford_multi(graph, 'ETH')
for path in paths:
    print_profit_opportunity_for_path_multi(graph, path)
