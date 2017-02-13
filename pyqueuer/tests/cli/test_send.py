#!/usr/bin/env python
# coding: utf-8

"""
Test CLI commands - "config"
"""

import unittest
from django.test import TestCase
from django.core.management import call_command
from django.core.management import CommandError
from django.conf import settings
from django.contrib.auth import authenticate
from pyqueuer.consts import ConfKeys, RabbitConfKeys, KafkaConfKeys
from pyqueuer.models import UserConf
import tempfile
import os
from ..base import MQTestMixin


class TestCLISend(TestCase, MQTestMixin):

    def setUp(self):
        call_command('init', password='123456', tester=True)
        self.tester = settings.TESTER
        self.user = authenticate(username=self.tester, password=self.tester)
        self.ucf = UserConf(self.user)
        self.mqtype = self.guess_mq_type(self.user)

    def tearDown(self):
        pass

    def test_send(self):
        name = pwd = self.tester
        mqtype = self.mqtype
        queue = self.ucf.get(ConfKeys[mqtype].queue_out)
        data = 'PyQueuer unittest sends message to queue.'

        # miss arguments
        with self.assertRaises(CommandError) as err:
            call_command('send', user=name, password=pwd)
        self.assertIn('arguments are required', str(err.exception))

        with self.assertRaises(CommandError) as err:
            call_command('send', user=name, password=pwd, queue=queue)
        self.assertIn('arguments are required', str(err.exception))

        with self.assertRaises(CommandError) as err:
            call_command('send', user=name, password=pwd, queue=queue, type=mqtype)
        self.assertIn('arguments are required', str(err.exception))

        # miss MQ type (even with incorrect arguments)
        rt = call_command('send', 'a=b', user=name, password=pwd)
        self.assertEqual(rt, 'You must specify MQ type.')

        # miss MQ type
        rt = call_command('send', 'queue=%s' % queue, user=name, password=pwd)
        self.assertEqual(rt, 'You must specify MQ type.')

        # miss data or file
        rt = call_command('send', 'queue=%s' % queue, user=name, password=pwd, type=mqtype)
        self.assertEqual(rt, 'You must specify either --data or --file for reading message.')

        # miss data or file (even with incorrect MQ type)
        rt = call_command('send', 'queue=%s' % queue, user=name, password=pwd, type=mqtype.lower())
        self.assertEqual(rt, 'You must specify either --data or --file for reading message.')

        # incorrect MQ type (even only lower case)
        with self.assertRaises(RuntimeError) as err:
            call_command('send', 'queue=%s' % queue, user=name, password=pwd, type=mqtype.lower(), data=data)
        self.assertIn('Unsupported MQ type', str(err.exception))

        rt = call_command('send', 'queue=%s' % queue, user=name, password=pwd, type=mqtype, data=data)
        self.assertIn('Message sent', rt)

    def test_send_to_exchange(self):
        name = pwd = self.tester
        mqtype = self.mqtype
        topic = self.ucf.get(ConfKeys[mqtype].topic_out)
        key = self.ucf.get(ConfKeys[mqtype].key_out)
        data = 'PyQueuer unittest sends message to exchange.'

        rt = call_command('send', 'topic=%s' % topic,  'key=%s' % key, user=name, password=pwd, type=mqtype, data=data)
        self.assertIn('Message sent', rt)

    def test_send_file(self):
        name = pwd = self.tester
        mqtype = self.mqtype
        queue = self.ucf.get(ConfKeys[mqtype].queue_out)
        file = os.path.sep.join([settings.BASE_DIR, 'tester.json'])
        rt = call_command('send', 'queue=%s' % queue, user=name, password=pwd, type=mqtype, file=file)
        self.assertIn('Message sent', rt)


if __name__ == '__main__':
    unittest.main()
