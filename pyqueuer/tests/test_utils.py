#!/usr/bin/env python
# coding: utf-8

"""
Tests for utils
"""

import unittest
from pyqueuer.utils import PropertyDict
from pyqueuer.utils import OutputBuffer
import datetime


class TestUtils(unittest.TestCase):

    def test_PropertyDict(self):
        x = PropertyDict(a=1, b=2, d=4, f=8)
        # for k, v in x.items():
        #     print('%s=%s' % (k, v), end=', ')
        self.assertEqual(x['a'], 1)
        self.assertEqual(x.b, 2)
        del x.a
        self.assertNotIn('a', x)
        x['c'] = 3
        self.assertEqual(x.c, 3)

        y = PropertyDict((
            ('a', 2),
            ('b', 4),
            ('c', 8),
        ))
        z = [x for x in y.values()]
        self.assertEqual(z[0], 2)
        self.assertEqual(z[2], 8)

        y['d'] = 16
        del y['b']
        z = [x for x in y.values()]
        self.assertEqual(z[2], 16)

    def test_OutputBuffer(self):
        buf = OutputBuffer(maxlen=5)
        self.assertTrue(buf.empty())
        self.assertFalse(buf.full())
        buf.write('message 1')
        self.assertEqual(len(buf), 1)
        buf.writelines([
            'line 2', 'line 3', 'line 4'
        ])
        self.assertEqual(4, len(buf))
        msg = buf.flush()
        self.assertEqual(4, len(msg))
        self.assertEqual('line 3', msg[1]['message'])

        buf.write('message 5')
        self.assertTrue(buf.full())
        self.assertFalse(buf.empty())
        buf.write('message 6')
        msg = buf.flush()
        t = datetime.datetime.utcnow()
        t1 = datetime.datetime.strptime(msg[0]['time'], '%Y-%m-%d %H:%M:%S.%f')
        self.assertEqual(t1.minute, t.minute)

if __name__ == '__main__':
    unittest.main()
