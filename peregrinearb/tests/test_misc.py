from unittest import TestCase
from peregrinearb.utils import misc


class TestMisc(TestCase):
    def test_elements_next_to_each_other(self):
        l = [0, 1, 2]
        self.assertTrue(misc.next_to_each_other(l, 1, 2))
