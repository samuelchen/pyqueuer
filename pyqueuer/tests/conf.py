#!/usr/bin/env python
# coding: utf-8

"""
Some configurations for testing
"""

from pyqueuer.utils import PropertyDict
from pyqueuer.mq import MQTypes
from pyqueuer.consts import ConfKeys, RabbitConfKeys, KafkaConfKeys, GeneralConfKeys
from django.conf import settings

# tester name & password
test_user = settings.TESTER if hasattr(settings, 'TESTER') else 'tester'

# tester settings
test_user_config = PropertyDict({
    GeneralConfKeys.data_store: "",
    GeneralConfKeys.result_store: "",

    RabbitConfKeys.host: "192.168.0.93",
    RabbitConfKeys.port: 5672,
    RabbitConfKeys.user: "test",
    RabbitConfKeys.password: "test",
    RabbitConfKeys.vhost: "/test",
    # RabbitConfKeys.queue_in: "test",
    # RabbitConfKeys.topic_in: "test",
    # RabbitConfKeys.key_in: "test",
    # RabbitConfKeys.queue_out: "test",
    # RabbitConfKeys.topic_out: "test",
    # RabbitConfKeys.key_out: "test",
    #
    # KafkaConfKeys.host: "192.168.0.93",
    # KafkaConfKeys.port: "9092",
    # KafkaConfKeys.topic_in: "test",
    # KafkaConfKeys.topic_out: "test",
})

# test materials
test_data = PropertyDict({
    "admin_pwd": "123456",
    "mq_type": MQTypes.RabbitMQ,

    MQTypes.RabbitMQ: {
        RabbitConfKeys.queue_in: "test",
        RabbitConfKeys.topic_in: "test",
        RabbitConfKeys.key_in: "test",
        RabbitConfKeys.queue_out: "test",
        RabbitConfKeys.topic_out: "test",
        RabbitConfKeys.key_out: "test",
    },

    MQTypes.Kafka: {
        KafkaConfKeys.host: "192.168.0.93",
        KafkaConfKeys.port: "9092",
        KafkaConfKeys.topic_in: "test",
        KafkaConfKeys.topic_out: "test",
    },
})
