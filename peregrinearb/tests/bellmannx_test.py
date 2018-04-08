from unittest import TestCase
from peregrinearb import bellman_ford_multi, multi_digraph_from_json, multi_digraph_from_dict, \
    calculate_profit_ratio_for_path, bellman_ford
import json
import networkx as nx


def graph_from_dict(graph_dict):
    if 'graph_type' not in graph_dict:
        raise ValueError('graph_dict must contain key "graph_type"')

    if graph_dict['graph_type'] == 'MultiDiGraph':
        return multi_digraph_from_dict(graph_dict['graph_dict'])
    elif graph_dict['graph_type'] == 'MultiGraph':
        return nx.from_dict_of_dicts(graph_dict['graph_dict'], multigraph_input=True)
    elif graph_dict['graph_type'] == 'DiGraph':
        return nx.from_dict_of_dicts(graph_dict['graph_dict'])
    elif graph_dict['graph_type'] == 'Graph':
        return nx.from_dict_of_dicts(graph_dict['graph_dict'])
    elif graph_dict['graph_type'] == 'other':
        return nx.from_dict_of_dicts(graph_dict['graph_dict'])
    else:
        raise ValueError("the value for 'graph_type' in graph_dict is not of the accepted values.")


def digraph_from_multi_graph_json(file_name):
    """
    file_name should hold a JSON which represents a MultiDigraph where there is a maximum of two edges each in opposing
    directions between each node
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
            new_graph, paths = bellman_ford_multi(graph, node)
            for path in paths:
                if path:
                    self.assertEqual(path[0], path[-1])

    def test_positive_ratio(self):
        graph = multi_digraph_from_json('test_multigraph.json')
        for node in graph:
            new_graph, paths = bellman_ford_multi(graph, node)
            for path in paths:
                if path:
                    # assert that the path is a negative weight cycle
                    ratio = calculate_profit_ratio_for_path(new_graph, path)
                    # python float precision may round some numbers to 1.0.
                    self.assertGreaterEqual(ratio, 1.0)

    def test_loop_from_source(self):
        graph = multi_digraph_from_json('test_multigraph.json')
        for node in graph:
            new_graph, paths = bellman_ford_multi(graph, node, loop_from_source=True)
            for path in paths:
                if path:
                    self.assertEqual(path[0], path[-1])
                    self.assertEqual(node, path[0])


class TestBellmannx(TestCase):

    def test_ensure_profit_yields_profit(self):
        graph = nx.DiGraph()
        graph.add_edge(0, 1, weight=4)
        graph.add_edge(1, 0, weight=3)
        graph.add_edge(1, 2, weight=-1)
        graph.add_edge(2, 3, weight=-1)
        graph.add_edge(3, 1, weight=-1)
        paths = bellman_ford(graph, 0, loop_from_source=True, ensure_profit=True)
        for path in paths:
            weight = 0
            for i in range(len(path) - 1):
                weight += graph[path[i]][path[i + 1]]['weight']
            self.assertLess(weight, 0)

    def test_depth(self):
        # currently does not work as bellman_ford is broken.
        for i in range(1, 5):
            G = nx.DiGraph()
            G.add_edge('A', 'B', weight=-0.69, depth=1)
            G.add_edge('B', 'C', weight=-1.1, depth=1)
            G.add_edge('C', 'A', weight=1.39, depth=i)
            paths = bellman_ford(G, 'A', unique_paths=True, depth=True)
            total = 0
            for path in paths:
                total += 1
            self.assertEquals(total, 0)
        for i in range(6, 8):
            G = nx.DiGraph()
            G.add_edge('A', 'B', weight=-0.69, depth=1)
            G.add_edge('B', 'C', weight=-1.1, depth=1)
            G.add_edge('C', 'A', weight=1.39, depth=i)
            paths = bellman_ford(G, 'A', unique_paths=True, depth=True)
            total = 0
            for path in paths:
                total += 1
            self.assertEquals(total, 1)
        # i = 0
        # for path in paths:
        #     i += 1
        #     # todo: because of python's floating point precision, calculate_profit_ratio_for_path returns 1.4918...
        #     # this is not the case with the normal call to bellman_ford, so figure out why this is different.
        #     self.assertEquals(1.5, calculate_profit_ratio_for_path(G, path))

