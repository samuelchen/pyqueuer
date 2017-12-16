#!/usr/bin/env python
# coding: utf-8

"""
Const variables
"""

from .utils import PropertyDict
from functools import reduce


MQTypes = PropertyDict(
    RabbitMQ='RabbitMQ',
    Kafka='Kafka'
)

# ---------------- Consts for settings ---------------
# NOTICE: const names must be unique.
# naming:
#     Basically we should use {type}_{usage}_{option} as name.
# ctor:
#     arg must be [("key", "value), ...] style to initialized ordered dict.
#     "key" would be the option attribute ref. It is NOT stored in DB. It's used in code to access as CONST.
#     "value" would be the option name. It is stored in DB as name. It's also displayed on UI.
# -----------------------------------------------------

# General config keys
GeneralConfKeys = PropertyDict([
    ('data_store', 'data_store'),
    ('result_store', 'result_store'),
])

# Configuration Keys mapping of pika RabbitMQ connection.
#
#     host (str) – Hostname or IP Address to connect to
#     port (int) – TCP port to connect to
#     vhost (str) – RabbitMQ virtual host to use (virtual_host)
#     user (str) – The username to authenticate with (username)
#     password (str) – The password to authenticate with
#
# unsupported:
#     channel_max (int) – Maximum number of channels to allow
#     frame_max (int) – The maximum byte size for an AMQP frame
#     heartbeat_interval (int) – How often to send heartbeats
#     ssl (bool) – Enable SSL
#     ssl_options (dict) – Arguments passed to ssl.wrap_socket as
#     connection_attempts (int) – Maximum number of retry attempts
#     retry_delay (int|float) – Time to wait in seconds, before the next
#     socket_timeout (int|float) – Use for high latency networks
#     locale (str) – Set the locale value
#     backpressure_detection (bool) – Toggle backpressure detection
RabbitConfKeys = PropertyDict([
    ('host', 'rabbit_host'),
    ('port', 'rabbit_port'),
    ('vhost', 'rabbit_vhost'),
    ('user', 'rabbit_user'),
    ('password', 'rabbit_password'),

    ('queue_in', 'rabbit_default_consuming_queue'),
    ('queue_out', 'rabbit_default_producing_queue'),
    ('topic_in', 'rabbit_default_consuming_topic_of_exchange'),
    ('topic_out', 'rabbit_default_producing_topic_of_exchange'),
    ('key_in', 'rabbit_default_consuming_key_for_topic_exchange'),
    ('key_out', 'rabbit_default_producing_key_for_topic_exchange'),
])

# Kafka config keys
KafkaConfKeys = PropertyDict([
    ('host', 'kafka_host'),
    ('port', 'kafka_port'),
    ('user', 'kafka_user'),
    ('password', 'kafka_password'),

    ('topic_in', 'kafka_default_consuming_topic'),
    ('topic_out', 'kafka_default_producing_topic'),
])


# all config keys in dict.
ConfKeys = PropertyDict([
    ('General', GeneralConfKeys),
    (MQTypes.RabbitMQ, RabbitConfKeys),
    (MQTypes.Kafka, KafkaConfKeys),
])
ConfKeys.key_count = reduce(lambda x, y: x + y, [len(keys) for keys in ConfKeys])