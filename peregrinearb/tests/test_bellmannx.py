import os
from unittest import TestCase
from peregrinearb import bellman_ford_multi, multi_digraph_from_json, multi_digraph_from_dict, \
    calculate_profit_ratio_for_path, bellman_ford, NegativeWeightFinder, NegativeWeightDepthFinder
from peregrinearb.bellmannx import get_starting_volume
import json
import networkx as nx
import math
import random
from ..utils import wss_add_market, wss_update_graph


def graph_from_dict(graph_dict):
    if 'graph_type' not in graph_dict:
        raise ValueError('graph_dict must contain key "graph_type"')

    # todo: use type() instead of this mess
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
        __location__ = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))
        graph = multi_digraph_from_json(os.path.join(__location__, 'test_multigraph.json'))
        for node in graph:
            new_graph, paths = bellman_ford_multi(graph, node)
            for path in paths:
                if path:
                    self.assertEqual(path[0], path[-1])

    def test_positive_ratio(self):
        __location__ = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))
        graph = multi_digraph_from_json(os.path.join(__location__, 'test_multigraph.json'))
        for node in graph:
            new_graph, paths = bellman_ford_multi(graph, node)
            for path in paths:
                if path:
                    # assert that the path is a negative weight cycle
                    ratio = calculate_profit_ratio_for_path(new_graph, path)
                    # python float precision may round some numbers to 1.0.
                    self.assertGreaterEqual(ratio, 1.0)


class TestBellmannx(TestCase):

    def setUp(self):
        self.edges_a = [
            # tail node, head node, no_fee_rate, depth (in terms of the first currency), trade_type
            ['A', 'B', 2, 3, 'SELL'],
            ['B', 'C', 3, 4, 'SELL'],
            ['C', 'A', 1 / 5, 14, 'SELL'],
        ]
        self.volume_scalar_a = 2 / 3

        self.edges_b = [
            # tail node, head node, no_fee_rate, depth (in terms of the first currency), trade_type
            # 5/6, 4/7, 5/6, 3/5
            ['A', 'B', 2, 3, 'SELL'],
            # ABC: 5/6 as limited by the price of A and the volume on B/C
            ['B', 'C', 3, 4, 'SELL'],
            # BCD:
            ['C', 'D', 7, 10, 'SELL'],
            ['D', 'E', 5, 40, 'SELL'],
            ['E', 'F', 1 / 5, 220, 'SELL'],
            ['F', 'G', 6, 40, 'SELL'],
            ['G', 'H', 1 / 20, 200, 'SELL'],
            ['H', 'A', 1 / 2, 20, 'SELL'],
        ]
        self.volume_scalar_b = (2 / 3) * (5 / 6) * (4 / 7) * (5 / 6)

    def test_get_starting_volume_a(self):
        """
        A simple test for get_starting_volume. Volume of the initial currency is limited only once. (on the B/C market)
        """
        graph = build_graph_from_edge_list(self.edges_a, 0)
        # the amount of currency A that can be used as limited by the market volumes
        expected_result = self.edges_a[0][3] * self.volume_scalar_a
        actual_result = get_starting_volume(graph, ['A', 'B', 'C', 'A'])
        self.assertAlmostEqual(actual_result, expected_result)

    def test_get_starting_volume_b(self):
        """
        Another test for get_starting_volume. Several markets limit the volume of the first currency in the path.
        """
        graph = build_graph_from_edge_list(self.edges_b, 0)
        # the amount of currency A that can be used as limited by the market volumes
        expected_result = self.edges_b[0][3] * self.volume_scalar_b
        actual_result = get_starting_volume(graph, [x[0] for x in self.edges_b] + [self.edges_b[0][0]])
        self.assertAlmostEqual(actual_result, expected_result)

    def test_returned_volume(self):
        """
        Tests the volume returned by NegativeWeightDepthFinder.bellman_ford
        """
        graph = build_graph_from_edge_list(self.edges_b, 0)
        finder = NegativeWeightDepthFinder(graph)
        opportunities = finder.bellman_ford('G', True)
        opportunities_found = 0
        for path, volume in opportunities:
            opportunities_found += 1

            self.assertGreater(len(path), 2, 'assert that there are at least 2 currencies in the path')
            self.assertGreater(volume, 0, 'assert that the maximum usable volume is at least 0')

            starting_edge_index = -1
            for i, edge in enumerate(self.edges_b):
                if edge[4].lower() != 'sell':
                    raise RuntimeError('This test expects only sell orders. There is an edge which is not a sell '
                                       'order: {}'.format(edge))
                if edge[0] == path[0]:
                    starting_edge_index = i
                    break
            # If this fails, something went very wrong or self.edges_b was changed.
            self.assertNotEqual(starting_edge_index, -1,
                                'assert that the first currency in the path is a part of an edge in self.edges_b')

            # used because of floating point precision
            diff_precision = 10 ** -8
            # how many orders use the maximum amount of possible volume
            orders_at_volume_capacity = 0
            for i in range(len(path) - 1):
                edge = self.edges_b[(starting_edge_index + i) % len(self.edges_b)]

                # difference between usable and used volume
                maximum_volume_diff = edge[3] - volume
                try:
                    self.assertGreater(maximum_volume_diff, -diff_precision,
                                       'assert that the volume used is less than the volume allowed by the market')
                except AssertionError as e:
                    raise e
                # if the volume used was within 10**-8 of the usable volume
                if abs(maximum_volume_diff) < diff_precision:
                    orders_at_volume_capacity += 1

                volume *= edge[2]
            self.assertGreater(orders_at_volume_capacity, 0,
                               'assert that all of the volume of at least one market is used')
        # assert that only one opportunity was found
        self.assertEqual(opportunities_found, 1)

    def test_negative_weight_depth_finder_a(self):
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

            for path, starting_amount in paths:
                # assert that if a path is found, only one is found.
                with self.assertRaises(StopIteration):
                    paths.__next__()

                ratio = calculate_profit_ratio_for_path(graph, path, depth=True,
                                                        starting_amount=starting_amount)

                self.assertAlmostEqual(ratio, edge_ratio)

    def test_negative_weight_depth_finder_b(self):
        """
        Another test for NegativeWeightDepthFinder
        """
        node_count = 30
        complete_graph = nx.complete_graph(node_count)
        graph = nx.DiGraph()
        for edge in complete_graph.edges():
            # Only use 1 / 3 of the edges, but use all edges connected to 0 to ensure all nodes reachable
            if random.random() < 2 / 3 and not (edge[0] == 0 or edge[1] == 0):
                continue

            random_weight = random.uniform(-10, 6)
            random_depth = random.uniform(0, 15)
            random_depth_b = random.uniform(-15, 0)
            if random_weight < 0:
                random_depth *= -1
                random_depth_b *= -1
            graph.add_edge(edge[0], edge[1], weight=random_weight, depth=random_depth)
            graph.add_edge(edge[1], edge[0], weight=-random_weight, depth=-random_depth_b)

        finder = NegativeWeightDepthFinder(graph)
        # does not matter which source is used, can be any number from 0 to 49. we use 0.
        paths = finder.bellman_ford(0)

        def calculate_ratio(found_path):
            total = 0
            for i in range(len(found_path) - 1):
                start = found_path[i]
                end = found_path[i + 1]
                total += graph[start][end]['weight']
            return total

        for path, starting_amount in paths:
            ratio = calculate_ratio(path)
            self.assertLess(ratio, 0.0)

    def test_negative_weight_depth_finder_c(self):
        """Tests NegativeWeightDepthFinder as it is used for arbitrage"""
        symbols = ['BTC/USD', 'ETH/USD', 'ETH/BTC', 'LTC/BTC', 'LTC/USD', 'ETH/LTC', 'DRC/BTC', 'DRC/ETH']
        markets = {symbol: {
            'volume_increment': 10 ** -8,
            'price_increment': 10 ** -8,
            'min_market_funds': 10 ** -16,
            'taker_fee': 0.001,
            'maker_fee': 0,
        } for symbol in symbols}
        graph = nx.DiGraph()
        [wss_add_market(graph, k, v) for k, v in markets.items()]
        wss_update_graph(graph, 'BTC/USD', 'asks', 5000, 0.5)
        wss_update_graph(graph, 'ETH/USD', 'bids', 500, 6)
        wss_update_graph(graph, 'ETH/BTC', 'asks', 0.14, 8)

        nwdf = NegativeWeightDepthFinder(graph)
        paths = nwdf.bellman_ford('BTC')
        for p in paths:
            print(p)

    def test_ratio(self):
        G = nx.DiGraph()
        G.add_edge('A', 'B', weight=-math.log(2))
        G.add_edge('B', 'C', weight=-math.log(3))
        G.add_edge('C', 'A', weight=-math.log(1 / 4))
        paths = bellman_ford(G, 'A', unique_paths=True)
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
