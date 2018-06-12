from unittest import TestCase
from peregrinearb import bellman_ford_multi, multi_digraph_from_json, multi_digraph_from_dict, \
    calculate_profit_ratio_for_path, bellman_ford, NegativeWeightFinder, NegativeWeightDepthFinder
import json
import networkx as nx
import math


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
            new_graph, paths = bellman_ford_multi(graph, node, loop_from_source=False)
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
        # currently does not work as bellman_ford's depth feature is broken/ in development.
        for i in range(1, 4):
            G = nx.DiGraph()
            # for the depth of A->B, 0 == -math.log(1). also note weight of A->B == depth B->C.
            G.add_edge('A', 'B', weight=-math.log(2), depth=0)
            G.add_edge('B', 'C', weight=-math.log(3), depth=-math.log(2))
            # there should be weight of 6 after going through A->B->C.
            G.add_edge('C', 'A', weight=-math.log(1/8), depth=-math.log(i))
            finder = NegativeWeightFinder(G, depth=True)
            paths = finder.bellman_ford('A', loop_from_source=False, unique_paths=True)

            total = 0
            for path in paths:
                self.assertLessEqual(1, calculate_profit_ratio_for_path(G, path, depth=True, starting_amount=1))

        for i in range(6, 8):
            G = nx.DiGraph()
            G.add_edge('A', 'B', weight=-math.log(2), depth=0)
            G.add_edge('B', 'C', weight=-math.log(3), depth=-math.log(2))
            G.add_edge('C', 'A', weight=-math.log(1 / 4), depth=-math.log(i))
            paths = bellman_ford(G, 'A', unique_paths=True, depth=True)

    def test_true_depth(self):
        """
        Tests NegativeWeightDepthFinder
        """
        # Tests that a negative loop starting at A cannot exist because the minimum weight of a cycle from and to A
        # is approximately 0.154, which is the negative log of 6/7.
        for i in range(1, 4):
            # todo: must we reinitialize G?
            G = nx.DiGraph()
            G.add_edge('A', 'B', weight=-math.log(2), depth=0)
            G.add_edge('B', 'C', weight=-math.log(3), depth=-math.log(2))
            G.add_edge('C', 'A', weight=-math.log(2 / 7), depth=-math.log(i))

            paths = NegativeWeightDepthFinder(G).bellman_ford('A')
            total = 0
            for path in paths:
                total += 1

            # asserts that there were no paths with negative weight given depths between -math.log(1) and -math.log(3)
            # for the edge C->A
            self.assertEqual(total, 0)

        total = 0
        for i in range(4, 7):
            G = nx.DiGraph()
            G.add_edge('A', 'B', weight=-math.log(2), depth=0)
            G.add_edge('B', 'C', weight=-math.log(3), depth=-math.log(2))
            G.add_edge('C', 'A', weight=-math.log(2 / 7), depth=-math.log(i))

            paths = NegativeWeightDepthFinder(G).bellman_ford('A')
            for path in paths:
                # asserts that each of the 3 paths has a profit ratio of 8/7, 10/7, and 12/7, respectively.
                # Because of Python float precision, the last digit of either value is sometimes not equal to the other.
                self.assertAlmostEqual(calculate_profit_ratio_for_path(G, path, depth=True), 8 / 7 + (i - 4) * (2/7))
                total += 1
        # asserts that there is a negatively-weighted path when the depth for the edge C->A < -math.log(4)
        self.assertEqual(total, 3)

    def test_ratio(self):
        G = nx.DiGraph()
        G.add_edge('A', 'B', weight=-math.log(2))
        G.add_edge('B', 'C', weight=-math.log(3))
        G.add_edge('C', 'A', weight=-math.log(1/4))
        paths = bellman_ford(G, 'A', unique_paths=True, loop_from_source=False)
        path_count = 0

        for path in paths:
            path_count += 1
            self.assertAlmostEqual(calculate_profit_ratio_for_path(G, path), 1.5)

        # assert that unique_paths allows for only one path
        self.assertEqual(path_count, 1)
