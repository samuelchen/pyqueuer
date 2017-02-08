#!/usr/bin/env python
# coding: utf-8

"""
Test CLI commands - "config"
"""

import unittest
from django.test import TestCase
from django.core.management import call_command
from django.conf import settings
from pyqueuer.models import ConfKeys


class TestCLIConfig(TestCase):

    def setUp(self):
        call_command('init', password='123456', tester=True)

    def tearDown(self):
        pass

    def test_config(self):
        name = pwd = settings.TESTER
        rt = call_command('config', user=name, password=pwd)
        self.assertEqual(rt, 'Please specify arguments such as --list or --get.')

        rt = call_command('config', user=name, password=pwd, list=True)
        lines = rt.split('\n')
        options = []
        for line in lines:
            opt = line.split('=')
            options.append(opt[0])
        for confs in ConfKeys.values():
            for key in confs.values():
                self.assertIn(key, options)

        call_command('config', 'data_store=/tmp/my_data_store', user=name, password=pwd)
        rt = call_command('config', user=name, password=pwd, get='data_store')
        self.assertEqual(rt, '/tmp/my_data_store')


if __name__ == '__main__':
    unittest.main()
