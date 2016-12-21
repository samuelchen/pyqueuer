#!/usr/bin/env python
# coding: utf-8

"""
Tests for utils
"""

import unittest
from pyqueuer.utils import PropertyDict


class TestUtils(unittest.TestCase):
    def test_PropertyDict(self):
        x = PropertyDict(a=1, b=2, d=4, f=8)
        for k, v in x.items():
            print('%s=%s' % (k, v), end=', ')
        self.assertEqual(x['a'], 1)
        self.assertEqual(x.b, 2)
        del x.a
        self.assertNotIn('a', x)
        x['c'] = 3
        self.assertEqual(x.c, 3)


if __name__ == '__main__':
    unittest.main()
