from peregrine import create_weighted_multi_exchange_digraph, bellman_ford_multi, \
    print_profit_opportunity_for_path_multi, load_exchange_graph, calculate_profit_for_path_multi, bellman_ford, print_profit_opportunity_for_path
import networkx as nx
import json
import asyncio

with open('graph.json', 'w') as outfile:
    json.dump(nx.to_dict_of_dicts(create_weighted_multi_exchange_digraph(['kraken'], log=True)), outfile)


def multi_digraph_from_json(file_name):
    with open(file_name) as f:
        data = json.load(f)
    
    G = nx.MultiDiGraph()
    for node in data.keys():
        neighbors = data[node]
        for neighbor, v in neighbors.items():
            for key, data_dict in v.items():
                G.add_edge(node, neighbor, **data_dict)
    
    return G


def digraph_from_multi_graph_json(file_name):
    """
    file_name should hold a JSON which represents a MultiDigraph which represents one exchange
    :param file_name:
    """
    with open(file_name) as f:
        data = json.load(f)

    G = nx.DiGraph()
    for node in data.keys():
        neighbors = data[node]
        for neighbor, v in neighbors.items():
            for key, data_dict in v.items():
                G.add_edge(node, neighbor, **data_dict)

    return G


graph = multi_digraph_from_json('graph.json')
graph, path = bellman_ford_multi(graph, 'EUR')
total = calculate_profit_for_path_multi(graph, path)
print(path)
print_profit_opportunity_for_path_multi(graph, path)
print("\n")


graph = digraph_from_multi_graph_json('graph.json')
# print(nx.to_dict_of_dicts(graph))
path = bellman_ford(graph, 'EUR')
print_profit_opportunity_for_path(graph, path)
