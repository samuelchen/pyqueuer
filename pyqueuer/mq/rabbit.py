#!/usr/bin/env python
# coding: utf-8
__author__ = 'Samuel Chen <samuel.net@gmail.com>'
__date__ = '10/27/2016 3:14 PM'

'''
rabbitmq module description

Created on 10/27/2016
'''

from .base import MQClient
from ..models import RabbitConfKeys
import pika
import logging
from time import sleep

log = logging.getLogger(__name__)


class RabbitMQBlockingClient(MQClient):
    _conn = None
    _channel_producing = None
    _channel_consuming = None

    _host = None
    _port = None
    _user = None
    _passwd = None
    _vhost = None

    def init(self, *args, **kwargs):

        try:
            self._host = self.config[RabbitConfKeys.host]
            self._port = int(self.config[RabbitConfKeys.port])
            self._user = self.config[RabbitConfKeys.user]
            self._passwd = self.config[RabbitConfKeys.password]
            self._vhost = self.config[RabbitConfKeys.vhost]
        except:
            raise Exception('You must specify the configurations in dict')

    def connect(self):
        try:
            if self._conn is None:
                credentials = pika.PlainCredentials(self._user, self._passwd)
                parameters = pika.ConnectionParameters(host=self._host, port=self._port, virtual_host=self._vhost,
                                                       credentials=credentials)
                self._conn = pika.BlockingConnection(parameters)
        except pika.exceptions.ConnectionClosed:
            log.warn('Fail connecting RabbitMQ server %s:%s.' % (self._host, self._port))

    def disconnect(self):
        if self._channel_consuming is not None:
            self._channel_consuming.close()

        if self._channel_producing is not None:
            self._channel_producing.close()

        if self._conn is not None:
            self._conn.close()

    def reconnect(self):
        pass

    def _get_producing_channel(self):
        self.connect()
        if self._channel_producing is None:
            self._channel_producing = self._conn.channel()
        return self._channel_producing

    def _get_consuming_channel(self):
        self.connect()
        if self._channel_consuming is None:
            self._channel_consuming = self._conn.channel()
        return self._channel_consuming

    # ------------------------
    # Basic methods
    # ------------------------

    def basic_get(self, queue):
        pass

    def basic_send(self, message, queue):
        pass

    def basic_ack(self):
        pass

    # ------------------------
    # High level methods
    # ------------------------

    def send_ex(self, msg, exchange, key):
        channel = self._get_producing_channel()

        channel.basic_publish(exchange,
                              key, msg,
                              pika.BasicProperties(
                                  content_type='application/json',
                                  delivery_mode=2))

        log.info('Message sent.')

    def send(self, msg, queue):
        channel = self._get_producing_channel()

        channel.basic_publish('', queue, msg,
                              pika.BasicProperties(
                                  content_type='application/json',
                                  delivery_mode=2))

        log.info('Message sent to queue "%s".' % queue)

    def consume_ex(self, exchange, key, callback, stop_event=None):
        channel = self._get_consuming_channel()
        channel.exchange_declare(exchange=exchange, type='topic')
        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        log.debug('consuming exchange queue %s' % queue_name)

        channel.queue_bind(exchange=exchange,
                           queue=queue_name,
                           routing_key=key)

        while True:
            method, properties, body = channel.basic_get(queue=queue_name, no_ack=True)
            if body:
                callback(body)
            if stop_event is None or stop_event.isSet():
                break
            sleep(1)

    def consume(self, queue, callback, stop_event=None, exchange=None, key=None):
        channel = self._get_consuming_channel()

        queue_name = queue
        if exchange is not None:
            channel.exchange_declare(exchange=exchange, type='topic')
        channel.queue_declare(queue=queue_name, durable=True)

        log.debug('consuming queue %s' % queue_name)

        if exchange is not None:
            channel.queue_bind(exchange=exchange,
                               queue=queue_name,
                               routing_key=key)

        while True:
            method, properties, body = channel.basic_get(queue=queue_name, no_ack=True)
            if body:
                callback(body)
            if stop_event is None or stop_event.isSet():
                break
            # print('consuming...')
            sleep(1)

