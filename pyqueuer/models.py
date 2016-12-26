#!/usr/bin/env python
# coding: utf-8

"""
models module defines the Django ORM models.
this module contains some constants as well.
"""

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from .utils import PropertyDict


# ---------------- Consts ---------------
# NOTICE: const names must be unique.
# naming:
#     Basically we should use {type}_{usage}_{option} as name.
# ctor:
#     arg must be [("key", "value), ...] style to initialized ordered dict.
#     "key" would be the option attribute ref. It is NOT stored in DB. It's used in code to access as CONST.
#     "value" would be the option name. It is stored in DB as name. It's also displayed on UI.
# ---------------------------------------

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
    # ('user', 'kafka_user'),
    # ('password', 'kafka_password'),

    ('topic_in', 'kafka_default_consuming_topic'),
    ('topic_out', 'kafka_default_producing_topic'),
])


# all config keys in dict.
ConfKeys = PropertyDict([
    ('general', GeneralConfKeys),
    ('rabbit', RabbitConfKeys),
    ('kafka', KafkaConfKeys),
])


# ----------- Models --------------

class BaseModel(models.Model):
    user = models.ForeignKey(User if not hasattr(settings, 'AUTH_USER_MODEL') else settings.AUTH_USER_MODEL)

    class Meta:
        abstract = True


class Config(BaseModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    value = models.TextField()

    class Meta:
        unique_together = ('user', 'name')


class PluginStackModel(BaseModel):
    id = models.AutoField(primary_key=True)
    stack = models.CharField(max_length=250)
    plugin = models.CharField(max_length=250)
    desc = models.TextField()

    class Meta:
        unique_together = ('user', 'stack', 'plugin')


# ---------- Utils -----------------

class UserConf(object):
    """
    The utility class for accessing user configuration.
    """

    _user = None

    def __init__(self, user):
        self._user = user

    def initialize(self):
        for section, conf in ConfKeys.items():
            for k, v in conf.items():
                obj, created = Config.objects.get_or_create(name=v, user=self._user)
                if created:
                    obj.value = ''
                    obj.save()

    def get(self, name):
        return Config.objects.get(name=name, user=self._user).value

    def set(self, name, value):
        obj, created = Config.objects.get_or_create(name=name, user=self._user)
        obj.value = value
        obj.save()

    def all(self):
        return Config.objects.filter(user=self._user)