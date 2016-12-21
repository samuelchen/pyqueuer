#!/usr/bin/env python
# coding: utf-8

"""
Tests for MQ
"""

import unittest
from pyqueuer.mq import MQTypes
from pyqueuer.mq.rabbit import RabbitConfKeys
from pyqueuer.mq import create_client
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
        self.mq = create_client(MQTypes.RabbitMQ, conf)
        self.mq.connect()

    def tearDown(self):
        self.mq.disconnect()

    # def test_send(self):
    #     msg = 'my first message.'
    #     self.mq.send(msg)
    #     self.assertEqual(True, True)


class KafkaTestCase(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
