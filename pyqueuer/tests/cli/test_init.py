#!/usr/bin/env python
# coding: utf-8

"""
Test CLI commands - "init"
"""

import unittest
from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import authenticate
from django.conf import settings

from pyqueuer.management.commands.init import Command as InitCommand
from pyqueuer.models import UserConf
import configparser


class TestCLIInit(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_init(self):
        name = 'admin'      # default name
        pwd = '123456'
        email = 'anonymous@localhost'
        call_command('init', password=pwd)
        admin = authenticate(username=name, password=pwd)
        self.assertIsNotNone(admin)
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertEqual(admin.email, email)

    def test_init_customized_admin(self):
        name = 'pyqueuer'
        pwd = '234567'
        email = 'pyqueuer@samuelchen.net'
        call_command('init', user=name, password=pwd, email=email)
        admin = authenticate(username=name, password=pwd)
        self.assertIsNotNone(admin)
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertEqual(admin.email, email)

    def test_init_tester(self):
        pwd = '234567'
        t = settings.TESTER
        email = 'anonymous@localhost'
        config_file = InitCommand.default_tester_config
        call_command('init', password=pwd, tester=True)
        tester = authenticate(username=t, password=t)
        self.assertIsNotNone(tester)
        self.assertTrue(tester.is_active)
        self.assertFalse(tester.is_superuser)
        self.assertFalse(tester.is_staff)
        self.assertEqual(tester.email, email)

        dummy_section = '_'
        ucf = UserConf(tester)
        cf = configparser.ConfigParser()
        with open(config_file, 'r') as f:
            config_string = '[%s]\n' % dummy_section + f.read()
        cf.read_string(config_string)
        for opt in ucf.all():
            v = cf.get(dummy_section, opt.name)
            self.assertEqual(v, opt.value)



if __name__ == '__main__':
    unittest.main()
