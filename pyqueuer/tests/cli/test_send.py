#!/usr/bin/env python
# coding: utf-8

"""
Test CLI commands - "config"
"""

import unittest
from django.test import TestCase
from django.core.management import call_command
from django.core.management import CommandError
from ..conf import test_user, test_data
from ...consts import ConfKeys, RabbitConfKeys, KafkaConfKeys


class TestCLISend(TestCase):

    def setUp(self):
        call_command('init', password=test_data['admin_pwd'], tester=True)
        self.mqtype = test_data['mq_type']
        self.testdata = test_data[self.mqtype]

    def tearDown(self):
        pass

    def test_send(self):
        name = pwd = test_user
        mqtype = self.mqtype
        queue = self.testdata[ConfKeys[mqtype].queue_out]
        data = 'PyQueuer unittest sends message.'

        # miss arguments
        with self.assertRaises(CommandError) as err:
            call_command('send', user=name, password=pwd)
        self.assertIn('arguments are required', str(err.exception))

        with self.assertRaises(CommandError) as err:
            call_command('send', user=name, password=pwd, queue=queue)
        self.assertIn('arguments are required', str(err.exception))

        with self.assertRaises(CommandError) as err:
            call_command('send', user=name, password=pwd, queue=queue, type=self.mqtype)
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

        call_command('send', 'queue=%s' % queue, user=name, password=pwd, type=mqtype, data=data)

        # rt = call_command('send', 'queue=test', user=name, password=pwd, type='RabbitMQ', data='PyQueuer unittest')
        # self.assertEqual(rt, 'You must specify either --data or --file for the message.')

        # self.assertRaises(RuntimeError, call_command, ('send', ), user=name, password=pwd,
        #                   type=mqtype, queue=queue, data=data)

        # rt = call_command('config', user=name, password=pwd, list=True)
        # lines = rt.split('\n')
        # options = []
        # for line in lines:
        #     opt = line.split('=')
        #     options.append(opt[0])
        # for confs in ConfKeys.values():
        #     for key in confs.values():
        #         self.assertIn(key, options)
        #
        # call_command('config', 'data_store=/tmp/my_data_store', user=name, password=pwd)
        # rt = call_command('config', user=name, password=pwd, get='data_store')
        # self.assertEqual(rt, '/tmp/my_data_store')


if __name__ == '__main__':
    unittest.main()
