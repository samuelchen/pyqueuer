#!/usr/bin/env python
# coding: utf-8

"""
Tests for MQ
"""

import unittest
from django.test import TestCase
from django.contrib.auth import authenticate
from django.core.management import call_command
from django.conf import settings
from pyqueuer.consts import MQTypes, ConfKeys
from pyqueuer.mq import MQClientFactory
from pyqueuer.models import UserConf
from .base import MQTestMixin


class TestRabbitMQ(TestCase, MQTestMixin):
    def setUp(self):
        call_command('init', password='123456', tester=True)

        tester = settings.TESTER
        self.user = authenticate(username=tester, password=tester)
        self.mqtype = MQTypes.RabbitMQ
        self.ucf = UserConf(self.user)
        conf = MQClientFactory.get_confs(self.mqtype, self.user)
        self.mq = MQClientFactory.create_connection(self.mqtype, conf)
        self.mq.connect()

    def tearDown(self):
        self.mq.disconnect()

    def test_send_to_queue(self):
        msg = 'my first test message.'
        producer = self.mq.create_producer()
        producer.produce(msg, queue=self.ucf.get(ConfKeys[self.mqtype].queue_out))
        self.mq.create_consumer()
        self.assertEqual(True, True)

    def test_send_to_exchange(self):
        msg = 'my second test message to topic & key.'
        producer = self.mq.create_producer()
        producer.produce(msg, topic=self.ucf.get(ConfKeys[self.mqtype].topic_out),
                         key=self.ucf.get(ConfKeys[self.mqtype].key_out))
        self.assertEqual(True, True)


class KafkaTestCase(TestCase):
    def setUp(self):
        call_command('init', password='123456', tester=True)

        tester = settings.TESTER
        self.user = authenticate(username=tester, password=tester)
        self.mqtype = MQTypes.Kafka
        self.ucf = UserConf(self.user)
        conf = MQClientFactory.get_confs(self.mqtype, self.user)
        self.mq = MQClientFactory.create_connection(self.mqtype, conf)
        self.mq.connect()

    def tearDown(self):
        self.mq.disconnect()

    def test_send_to_queue(self):
        msg = 'my first test message.'
        producer = self.mq.create_producer()
        producer.produce(msg, topic=self.ucf.get(ConfKeys[self.mqtype].topic_out))
        self.mq.create_consumer()
        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
