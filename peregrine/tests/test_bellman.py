from unittest import TestCase
from peregrine.bellman import get_all_paths_for_graph, calculate_profit_ratio_for_path
import math


def within_one_percent(x, y):
    return .99 * x < y < 1.01 * x


class TestBellmanFord(TestCase):

    def test_calculate_profit_ratio_for_path(self):
        """
        a------2----->b
        ^            /
         \          /
         1/3       3
           \    /
            \  ▼
              c

        """
        graph = {'a': {'b': -math.log(2), 'c': math.log(1 / 3)},
                 'b': {'a': math.log(2), 'c': -math.log(3)},
                 'c': {'a': -math.log(1 / 3), 'b': math.log(3)}}

        paths = get_all_paths_for_graph(graph)
        for path in paths:
            ratio = calculate_profit_ratio_for_path(graph, path)
            # because Python float precision, ratio == 1.9999999999999996
            self.assertTrue(within_one_percent(ratio, 2))
