from unittest import TestCase
from peregrinearb import bellman_ford_multi, multi_digraph_from_json, multi_digraph_from_dict, \
    calculate_profit_ratio_for_path, bellman_ford, NegativeWeightFinder, NegativeWeightDepthFinder, \
    print_profit_opportunity_for_path
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


def build_graph_from_edge_list(edges, fee):
    graph = nx.DiGraph()
    for edge in edges:
        sell = edge[4] == 'SELL'
        graph.add_edge(
            edge[0], edge[1], weight=-math.log(edge[2] * (1 - fee)), depth=-math.log(edge[3]), trade_type=edge[4],
            fee=fee, no_fee_rate=edge[2] if sell else 1 / edge[2],
            market_name='{}/{}'.format(edge[0], edge[1]) if sell else '{}/{}'.format(edge[1], edge[0])
        )

    return graph


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
        """
        Does not work, as this parameter (ensure_profit) was deprecated
        """
        pass
        # graph = nx.DiGraph()
        # graph.add_edge(0, 1, weight=4)
        # graph.add_edge(1, 0, weight=3)
        # graph.add_edge(1, 2, weight=-1)
        # graph.add_edge(2, 3, weight=-1)
        # graph.add_edge(3, 1, weight=-1)
        # paths = bellman_ford(graph, 0, loop_from_source=True, ensure_profit=True)
        # for path in paths:
        #     weight = 0
        #     for i in range(len(path) - 1):
        #         weight += graph[path[i]][path[i + 1]]['weight']
        #     self.assertLess(weight, 0)
        #
        # for i in range(6, 8):
        #     G = nx.DiGraph()
        #     G.add_edge('A', 'B', weight=-math.log(2), depth=0)
        #     G.add_edge('B', 'C', weight=-math.log(3), depth=-math.log(2))
        #     G.add_edge('C', 'A', weight=-math.log(1 / 4), depth=-math.log(i))
        #     paths = bellman_ford(G, 'A', unique_paths=True)

    def test_negative_weight_depth(self):
        """
        Tests NegativeWeightDepthFinder
        """
        final_edge_weight = 0.25
        edges = [
            # tail node, head node, no_fee_rate, depth (in terms of profited currency), trade_type
            ['A', 'B', 2, 3, 'SELL'],
            ['B', 'C', 3, 4, 'SELL'],
            ['C', 'D', 1 / 7, 14, 'BUY'],
            ['D', 'E', 0.2, 3 / 2, 'BUY'],
            ['E', 'F', 4, 3, 'SELL'],
            ['F', 'G', 6, 0.8, 'BUY'],
            ['G', 'H', 0.75, 6, 'BUY'],
            ['H', 'A', final_edge_weight, 20, 'BUY'],
        ]
        fee = 0.01

        # ratio for the rates from A -> H
        def get_edge_ratio():
            constant_ratio = 1
            for edge in edges:
                constant_ratio *= edge[2] * (1 - fee)
            return constant_ratio

        for i in range(10):
            edges[-1][2] = final_edge_weight * (i + 1)
            graph = build_graph_from_edge_list(edges, fee)
            finder = NegativeWeightDepthFinder(graph)
            paths = finder.bellman_ford('A')

            edge_ratio = get_edge_ratio()
            if edge_ratio <= 1:
                with self.assertRaises(StopIteration):
                    paths.__next__()

            for path in paths:
                # assert that if a path is found, only one is found.
                with self.assertRaises(StopIteration):
                    paths.__next__()

                ratio = calculate_profit_ratio_for_path(graph, path['loop'], depth=True,
                                                        starting_amount=math.exp(-path['minimum']))

                self.assertAlmostEqual(ratio, edge_ratio)

    def test_ratio(self):
        G = nx.DiGraph()
        G.add_edge('A', 'B', weight=-math.log(2))
        G.add_edge('B', 'C', weight=-math.log(3))
        G.add_edge('C', 'A', weight=-math.log(1 / 4))
        paths = bellman_ford(G, 'A', unique_paths=True, loop_from_source=False)
        path_count = 0

        for path in paths:
            path_count += 1
            self.assertAlmostEqual(calculate_profit_ratio_for_path(G, path), 1.5)

        # assert that unique_paths allows for only one path
        self.assertEqual(path_count, 1)


class TestCalculateProfitRatioForPath(TestCase):

    def test_calculate_profit_ratio_for_path(self):
        graph = nx.DiGraph()
        edges = [
            # tail node, head node, no_fee_rate, depth (in terms of currency traded), trade_type
            ['A', 'B', 2, 3, 'SELL'],
            ['B', 'C', 3, 4, 'SELL'],
            ['C', 'D', 1 / 7, 14, 'BUY'],
            ['D', 'E', 0.2, 3 / 2, 'BUY'],
            ['E', 'F', 4, 3, 'SELL'],
            ['F', 'G', 6, 0.8, 'BUY'],
            ['G', 'H', 0.75, 6, 'BUY'],
            ['H', 'A', 3, 20, 'BUY'],
        ]
        fee = 0.01

        for edge in edges:
            sell = edge[4] == 'SELL'
            graph.add_edge(
                edge[0], edge[1], weight=-math.log(edge[2] * (1 - fee)), depth=-math.log(edge[3]), trade_type=edge[4],
                fee=fee, no_fee_rate=edge[2] if sell else 1 / edge[2],
                market_name='{}/{}'.format(edge[0], edge[1]) if sell else '{}/{}'.format(edge[1], edge[0])
            )

        path = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'A']
        starting_amount = 3
        ratio, path_data = calculate_profit_ratio_for_path(graph, path, depth=True,
                                                           starting_amount=starting_amount, gather_path_data=True)

        self.assertEqual(path_data[0]['rate'], 2)
        self.assertEqual(path_data[0]['volume'], 3)
        self.assertEqual(path_data[0]['order'], 'SELL')

        self.assertEqual(path_data[1]['rate'], 3)
        self.assertEqual(path_data[1]['volume'], 4)
        self.assertEqual(path_data[1]['order'], 'SELL')

        self.assertEqual(path_data[2]['rate'], 7)
        # AlmostEqual, because of math.log, path_data[2]['volume'] == 1.697142857142857. 11.88 / 7 == 1.6971428571428573
        self.assertAlmostEqual(path_data[2]['volume'], 11.88 / 7)
        self.assertEqual(path_data[2]['order'], 'BUY')

        self.assertEqual(path_data[3]['rate'], 5)
        self.assertEqual(path_data[3]['volume'], 0.3)
        self.assertEqual(path_data[3]['order'], 'BUY')

        self.assertEqual(path_data[4]['rate'], 4)
        self.assertEqual(path_data[4]['volume'], 0.297)
        self.assertEqual(path_data[4]['order'], 'SELL')

        self.assertEqual(path_data[5]['rate'], 1 / 6)
        # If Equal instead of AlmostEqual, will raise 4.800000000000001 != 4.8
        self.assertAlmostEqual(path_data[5]['volume'], 4.8)
        self.assertEqual(path_data[5]['order'], 'BUY')

        self.assertEqual(path_data[6]['rate'], 4 / 3)
        self.assertAlmostEqual(path_data[6]['volume'], 4.8 * 0.99 * 0.75)
        self.assertEqual(path_data[6]['order'], 'BUY')

        self.assertEqual(path_data[7]['rate'], 1 / 3)
        self.assertAlmostEqual(path_data[7]['volume'], 3.564 * 0.99 * 3)
        self.assertEqual(path_data[7]['order'], 'BUY')

        self.assertAlmostEqual(ratio, 3.564 * 0.99 * 3 * 0.99 / starting_amount)
