from unittest import TestCase
from peregrinearb import format_graph_for_json
import networkx as nx


class TestUtils(TestCase):

    def test_write_graph_to_json(self):
        types = ['MultiDiGraph', 'MultiGraph', 'DiGraph', 'Graph']
        for t in types:
            g = getattr(nx, t)()
            d = format_graph_for_json(g)
            self.assertEqual(d['graph_type'], t)

        types = ['OrderedMultiDiGraph', 'OrderedMultiGraph', 'OrderedDiGraph']
        for t in types:
            g = getattr(nx, t)()
            with self.assertRaises(TypeError):
                d = format_graph_for_json(g)

            d = format_graph_for_json(g, raise_errors=False)
            self.assertEqual(d['graph_type'], 'other')


