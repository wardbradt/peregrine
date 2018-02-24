from peregrine import create_weighted_multi_exchange_digraph, bellman_ford_multi, \
    print_profit_opportunity_for_path_multi, calculate_profit_for_path_multi


graph = create_weighted_multi_exchange_digraph(['kraken', 'gemini', 'bittrex', 'okex'], log=True)
graph, path = bellman_ford_multi(graph, 'EUR')
total = calculate_profit_for_path_multi(graph, path)
print(path)
print_profit_opportunity_for_path_multi(graph, path)


# graph = digraph_from_multi_graph_json('graph.json')
# # print(nx.to_dict_of_dicts(graph))
# path = bellman_ford(graph, 'EUR')
# print_profit_opportunity_for_path(graph, path)
