from unittest import TestCase
from peregrine import bellman_ford_multi, create_weighted_multi_exchange_digraph, calculate_profit_for_path_multi
import json
import networkx as nx


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


class TestBellmanFordMultiGraph(TestCase):

    def test_path_beginning_equals_end(self):
        graph = multi_digraph_from_json('test_multigraph.json')
        for node in graph:
            new_graph, path = bellman_ford_multi(graph, node)
            if path:
                self.assertEqual(path[0], path[-1])

    def test_positive_ratio(self):
        graph = multi_digraph_from_json('test_multigraph.json')
        for node in graph:
            new_graph, path = bellman_ford_multi(graph, node)
            if path:
                # assert that the path is a negative weight cycle
                ratio = calculate_profit_for_path_multi(new_graph, path)
                self.assertGreater(ratio, 1.0)

    def test_loop_from_source(self):
        graph = multi_digraph_from_json('test_multigraph.json')
        for node in graph:
            new_graph, path = bellman_ford_multi(graph, node, loop_from_source=True)
            print(path)
            if path:
                self.assertEqual(path[0], path[-1])
                self.assertEqual(node, path[0])

