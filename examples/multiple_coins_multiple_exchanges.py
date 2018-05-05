from peregrinearb import create_weighted_multi_exchange_digraph, bellman_ford_multi, calculate_profit_ratio_for_path, \
    print_profit_opportunity_for_path_multi


graph = create_weighted_multi_exchange_digraph(['bittrex', 'gemini', 'kraken'], log=True)

graph, paths = bellman_ford_multi(graph, 'ETH', loop_from_source=False, unique_paths=True)
for path in paths:
    # total = calculate_profit_ratio_for_path(graph, path)
    # print(path)
    print_profit_opportunity_for_path_multi(graph, path)
