#!/usr/bin/env python
# coding: utf-8

"""
Test CLI commands - "config"
"""

import unittest
from django.test import TestCase
from django.core.management import call_command
from ..conf import test_user, test_user_config, test_data


class TestCLIConfig(TestCase):

    def setUp(self):
        call_command('init', password=test_data['admin_pwd'], tester=True)

    def tearDown(self):
        pass

    def test_config(self):
        name = pwd = test_user
        rt = call_command('config', user=name, password=pwd)
        self.assertEqual(rt, 'Please specify arguments such as --list or --get.')

        rt = call_command('config', user=name, password=pwd, list=True)
        lines = rt.split('\n')
        options = []
        for line in lines:
            opt = line.split('=')
            options.append(opt[0])
        for key in test_user_config.keys():
            self.assertIn(key, options)

        call_command('config', 'data_store=/tmp/my_data_store', user=name, password=pwd)
        rt = call_command('config', user=name, password=pwd, get='data_store')
        self.assertEqual(rt, '/tmp/my_data_store')


if __name__ == '__main__':
    unittest.main()
