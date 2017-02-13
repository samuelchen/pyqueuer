#!/usr/bin/env python
# coding: utf-8

"""
Test CLI commands - "config"
"""

import unittest
from django.test import TestCase
from django.core.management import call_command
from django.conf import settings
import os
from pyqueuer.consts import ConfKeys


class TestCLIConfig(TestCase):

    def setUp(self):
        call_command('init', password='123456', tester=True)

    def tearDown(self):
        pass

    def test_config(self):
        name = pwd = settings.TESTER
        rt = call_command('config', user=name, password=pwd)
        self.assertIn('Please specify arguments', rt)

        rt = call_command('config', user=name, password=pwd, list=True)
        lines = rt.split('\n')
        options = []
        for line in lines:
            opt = line.split('=')
            options.append(opt[0])
        for confs in ConfKeys.values():
            for key in confs.values():
                self.assertIn(key, options)

        rt = call_command('config', 'data_store=/tmp/my_data_store', user=name, password=pwd)
        self.assertIn('Configuration modified', rt)

        rt = call_command('config', user=name, password=pwd, get='data_store')
        self.assertEqual(rt, '/tmp/my_data_store')

    def test_config_import_export(self):
        name = pwd = settings.TESTER
        config_file = '/tmp/pyqueuer_config_export_text.ini'
        if os.path.exists(config_file):
            os.remove(config_file)

        # rt = call_command('config', user=name, password=pwd, list=True)
        # with open(config_file, 'wt') as f:
        #     f.write(rt)
        call_command('config', user=name, password=pwd, export=True, config_file=config_file)

        options = {
            "user": name,
            "password": pwd,
            "import": True,
            "config_file": config_file,
        }
        rt = call_command('config', **options)
        self.assertIn('Configuration modified', rt)
        os.remove(config_file)
        rt = call_command('config', **options)
        self.assertIn('File is not accessible', rt)


if __name__ == '__main__':
    unittest.main()
