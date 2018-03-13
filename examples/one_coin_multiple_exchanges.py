from peregrine import create_weighted_multi_exchange_digraph, bellman_ford_multi, calculate_profit_ratio_for_path, \
    print_profit_opportunity_for_path


graph = create_weighted_multi_exchange_digraph(['bittrex', 'gemini', 'kraken'], log=True)

graph, paths = bellman_ford_multi(graph, 'BTC')
for path in paths:
    total = calculate_profit_ratio_for_path(graph, path)
    print(path)
    print_profit_opportunity_for_path(graph, path)
