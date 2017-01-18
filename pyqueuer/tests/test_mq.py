#!/usr/bin/env python
# coding: utf-8

"""
Tests for MQ
"""

import unittest
from pyqueuer.mq import MQTypes
from pyqueuer.mq.rabbit import RabbitConfKeys
from pyqueuer.mq import MQClientFactory
from .conf import conf_rabbit


class TestRabbitMQ(unittest.TestCase):
    def setUp(self):
        conf = {
            RabbitConfKeys.host: conf_rabbit.host,
            RabbitConfKeys.port: conf_rabbit.port,
            RabbitConfKeys.user: conf_rabbit.user,
            RabbitConfKeys.password: conf_rabbit.password,
            RabbitConfKeys.vhost: conf_rabbit.vhost,
        }
        self.mq = MQClientFactory.create_connection(MQTypes.RabbitMQ, conf)
        self.mq.connect()

    def tearDown(self):
        self.mq.disconnect()

    def test_send_to_queue(self):
        msg = 'my first message.'
        producer = self.mq.create_producer()
        producer.produce(msg, queue=conf_rabbit.queue_out)
        consumer = self.mq.create_consumer()
        self.assertEqual(True, True)

    def test_send_to_exchange(self):
        msg = 'my second message to topic & key.'
        producer = self.mq.create_producer()
        producer.produce(msg, topic=conf_rabbit.topic_out, key=conf_rabbit.key_out)
        self.assertEqual(True, True)


class KafkaTestCase(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
