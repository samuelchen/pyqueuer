#!/usr/bin/env python
# coding: utf-8

"""
Tests for MQ
"""

import unittest
from django.test import TestCase
from django.contrib.auth import authenticate
from django.core.management import call_command
from pyqueuer.mq import MQTypes
from pyqueuer.mq import MQClientFactory
from .conf import test_user, test_data


class TestRabbitMQ(TestCase):
    def setUp(self):

        call_command('init', password=test_data['admin_pwd'], tester=True)

        self.mqtype = MQTypes.RabbitMQ
        self.user = authenticate(username=test_user, password=test_user)
        conf = MQClientFactory.get_confs(self.mqtype, self.user)
        self.mq = MQClientFactory.create_connection(MQTypes.RabbitMQ, conf)
        self.mq.connect()
        self.testdata = test_data[self.mqtype]

    def tearDown(self):
        self.mq.disconnect()

    def test_send_to_queue(self):
        msg = 'my first message.'
        producer = self.mq.create_producer()
        producer.produce(msg, queue=self.testdata['queue_out'])
        self.mq.create_consumer()
        self.assertEqual(True, True)

    def test_send_to_exchange(self):
        msg = 'my second message to topic & key.'
        producer = self.mq.create_producer()
        producer.produce(msg, topic=self.testdata['topic_out'], key=self.testdata['key_out'])
        self.assertEqual(True, True)


class KafkaTestCase(TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
