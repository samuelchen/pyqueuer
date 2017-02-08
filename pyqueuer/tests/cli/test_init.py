#!/usr/bin/env python
# coding: utf-8

"""
Test CLI commands - "init"
"""

import unittest
from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import authenticate
from ..conf import test_user


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
        t = test_user
        email = 'anonymous@localhost'
        call_command('init', password=pwd, tester=True)
        tester = authenticate(username=t, password=t)
        self.assertIsNotNone(tester)
        self.assertTrue(tester.is_active)
        self.assertFalse(tester.is_superuser)
        self.assertFalse(tester.is_staff)
        self.assertEqual(tester.email, email)


if __name__ == '__main__':
    unittest.main()
