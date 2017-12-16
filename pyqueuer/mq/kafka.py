#!/usr/bin/env python
# coding: utf-8

"""
kafka modules defines Kafka client classes
"""

from .base import IConnect, IProduce, IConsume
from ..consts import KafkaConfKeys
import kafka
import logging
log = logging.getLogger(__name__)


class KafkaConnection(IConnect):

    _host = None
    _port = None
    _user = None
    _password = None

    _producer = None
    _consumer = None

    def init(self):
        try:
            self._host = self.config[KafkaConfKeys.host]
            self._port = int(self.config[KafkaConfKeys.port])
            self._user = self.config[KafkaConfKeys.user]
            self._password = self.config[KafkaConfKeys.password]
        except KeyError as err:
            log.exception(err)
            raise Exception('You must specify the configurations in dict')

    def connect(self):
        # No need to connect
        pass

    def disconnect(self):
        # No need to disconnect
        pass

    def create_producer(self):
        return KafkaProducer(conn=self)

    def create_consumer(self):
        return KafkaConsumer(conn=self)

    # -- additional methods

    def create_sender(self):
        """create a kafka-python lib producer"""
        sender = kafka.KafkaProducer(bootstrap_servers=['%s:%s' % (self._host, self._port)],
                                     sasl_mechanism='SASL_PLAINTEXT',
                                     sasl_plain_username=self._user,
                                     sasl_plain_password=self._password)
        return sender

    def create_receiver(self):
        """create a kafka-python lib consumer"""
        receiver = kafka.KafkaConsumer(bootstrap_servers=['%s:%s' % (self._host, self._port)],
                                       sasl_mechanism='SASL_PLAINTEXT',
                                       sasl_plain_username=self._user,
                                       sasl_plain_password=self._password)
        return receiver


class KafkaProducer(IProduce):

    _sender = None

    # ------------------------
    # Properties
    # ------------------------

    @property
    def sender(self):
        if not self._sender:
            self._sender = self.connection.create_sender()
        return self._sender

    # ------------------------
    # Basic methods
    # ------------------------

    def basic_send(self, message, **kwargs):
        raise NotImplementedError

    # ------------------------
    # High level methods
    # ------------------------

    def produce(self, message, **kwargs):
        assert 'topic' in kwargs
        topic = kwargs['topic']
        key = kwargs['key'] if 'key' in kwargs else None

        log.debug('Sending message to "%s" : %s' % (topic, message))

        message_bytes = bytes(message, 'utf-8')
        if key:
            key_bytes = bytes(key, 'utf-8')
            future = self.sender.send(topic, key=key_bytes, value=message_bytes)
        else:
            future = self.sender.send(topic, message_bytes)

        try:
            record_metadata = future.get(timeout=10)
            log.info('Message sent.')
            log.debug(record_metadata)
        except kafka.KafkaError as err:
            log.exception('Message is not sent. %s' % err)


class KafkaConsumer(IConsume):

    _receiver = None

    # ------------------------
    # Properties
    # ------------------------
    @property
    def receiver(self):
        if not self._receiver:
            self._receiver = self.connection.create_receiver()
        return self._receiver

    # ------------------------
    # Basic methods
    # ------------------------

    def basic_ack(self, **kwargs):
        raise NotImplementedError

    def basic_get(self, **kwargs):
        raise NotImplementedError

    # ------------------------
    # High level methods
    # ------------------------

    def consume(self, **kwargs):
        assert 'topic' in kwargs
        topic = kwargs['topic']
        # group = kwargs['group'] if 'group' in kwargs else None
        callback = kwargs['callback'] if 'callback' in kwargs else lambda x: log.debug('Received message:  %s' % x)
        stop_event = kwargs['stop_event'] if 'stop_event' in kwargs else None

        self.receiver.subscribe([topic, ])

        for msg in self.receiver:
            log.debug(msg)
            try:
                # callback(str(msg.value, encoding='utf-8'))
                callback(msg.value)
            except Exception as err:
                log.exception(err)
            if stop_event is not None and stop_event.is_set():
                break
