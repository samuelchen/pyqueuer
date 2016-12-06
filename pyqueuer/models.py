from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from .utils import PropertyDict
import os
import simplejson as json
from collections import namedtuple, OrderedDict

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
    name = models.CharField(primary_key=True, max_length=100)
    value = models.TextField()


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


# class Setting(object):
#     _file = os.path.abspath(os.path.sep.join([os.path.dirname(os.path.abspath(__name__)), 'setting.json']))
#     _settings = {}
#
#     @staticmethod
#     def load():
#         with open(Setting._file) as f:
#             s = f.read()
#             Setting._settings = json.loads(s)
#
#     @staticmethod
#     def save():
#         with open(Setting._file, 'w') as f:
#             f.write(json.dumps(Setting._settings))
#
#     @staticmethod
#     def initialize():
#         for k in SETTING_NAMES:
#             Setting._settings[k] = ''
#         Setting.save()
#
#     @staticmethod
#     def get(name):
#         return Setting._settings[name]
#
#     @staticmethod
#     def set(name, value):
#         Setting._settings[name] = value
#
#     @staticmethod
#     def all():
#         return Setting._settings
#
# if not os.path.exists(Setting._file):
#     Setting.initialize()
#
# Setting.load()