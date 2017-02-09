#!/usr/bin/env python
# coding: utf-8

"""
RabbitMQ client module
"""

from .base import IConnect, IProduce, IConsume
from .base import MQAuthorizeException, MQConnectException
from ..consts import RabbitConfKeys
import pika
import logging
from time import sleep

log = logging.getLogger(__name__)


class RabbitMQConnection(IConnect):
    _conn = None

    _host = None
    _port = None
    _user = None
    _password = None
    _vhost = None

    def init(self, *args, **kwargs):

        try:
            self._host = self.config[RabbitConfKeys.host]
            self._port = int(self.config[RabbitConfKeys.port] or 5672)
            self._user = self.config[RabbitConfKeys.user]
            self._password = self.config[RabbitConfKeys.password]
            self._vhost = self.config[RabbitConfKeys.vhost]
        except KeyError as err:
            raise KeyError('You must specify the configurations in a dict. %s' % err)

    def connect(self):
        retries = 0
        interval = 2
        while self._conn is None:
            try:
                retries += 1
                credentials = pika.PlainCredentials(self._user, self._password)
                parameters = pika.ConnectionParameters(host=self._host, port=self._port, virtual_host=self._vhost,
                                                       credentials=credentials)
                self._conn = pika.BlockingConnection(parameters)
            except pika.exceptions.ConnectionClosed:
                if retries >= 3 or not self.auto_reconnect:
                    raise MQConnectException('Can not connect RabbitMQ %s:%s' % (self._host, self._port))
                else:
                    log.warn('Fail connecting RabbitMQ server %s:%s. Retry in %d seconds.'
                             % (self._host, self._port, interval))
                    sleep(interval)
                    interval *= 2
            except pika.exceptions.ProbableAuthenticationError:
                raise MQAuthorizeException('You are not authorized as user "%s" at virtual host "%s" on RabbitMQ %s:%s'
                                           % (self._user, self._vhost, self._host, self._port))

    def disconnect(self):
        if self._conn is not None:
            self._conn.close()

    def create_producer(self):
        return RabbitMQProducer(conn=self)

    def create_consumer(self):
        return RabbitMQConsumer(conn=self)

    # -- additional methods --

    def open_channel(self):
        if self.auto_reconnect and (not self._conn or not self._conn.is_open):
            self.connect()
        return self._conn.channel()


class RabbitMQProducer(IProduce):

    _channel = None

    # ------------------------
    # Properties
    # ------------------------
    @property
    def channel(self):
        if not self._channel or self._channel.is_closed:
            self._channel = self.connection.open_channel()
        return self._channel

    # ------------------------
    # Basic methods
    # ------------------------

    def basic_send(self, message, **kwargs):
        raise NotImplementedError

    # ------------------------
    # High level methods
    # ------------------------

    def produce(self, message, **kwargs):
        """
        Send message with given keyword args.
        :param message: Message to be sent.
        :param kwargs: "queue" or "topic" + "key". If all specified, accept "queue".
                        "content_type" (optional): Specify content type. Default is "plain/text".
                        "mode" (optional): Specify delivery mode. Default is 2. (Check Rabbit Doc)
        :return:
        """
        log.debug('Sending message "%s"' % message)
        assert message is not None
        channel = self.channel

        assert 'queue' in kwargs or ('topic' in kwargs and 'key' in kwargs)
        queue = kwargs['queue'] if 'queue' in kwargs else None
        topic = kwargs['topic'] if 'topic' in kwargs else None
        key = kwargs['key'] if 'key' in kwargs else None
        content_type = kwargs['content_type'] if 'content_type' in kwargs else 'plain/text'
        mode = kwargs['mode'] if 'mode' in kwargs else 2

        if queue:
            channel.basic_publish('', queue, message,
                                  pika.BasicProperties(
                                      content_type=content_type,
                                      delivery_mode=mode))
            log.info('Message sent to queue "%s".' % queue)
        elif topic and key:
            channel.basic_publish(topic,
                                  key, message,
                                  pika.BasicProperties(
                                      content_type=content_type,
                                      delivery_mode=mode))
            log.info('Message sent to exchange topic "%s" key "%s".' % (topic, key))
        else:
            raise ValueError('You must specify either "queue" or "topic"+"key" arguments.')
        # channel.close()
        # self._channel = None

    # def close(self):
    #     if self._channel:
    #         self._channel.close()
    #     self._channel = None


class RabbitMQConsumer(IConsume):

    _channel = None
    _stop_flag = False

    # ------------------------
    # Properties
    # ------------------------
    @property
    def channel(self):
        if not self._channel:
            self._channel = self.connection.open_channel()
        return self._channel

    # ------------------------
    # Basic methods
    # ------------------------

    def basic_get(self, **kwargs):
        raise NotImplementedError

    def basic_ack(self, **kwargs):
        raise NotImplementedError

    # ------------------------
    # High level methods
    # ------------------------

    def consume(self, **kwargs):
        """
        :param kwargs: "queue" or "topic" + "key". If all specified, accept "queue".
                        "callback" (optional): Callback function accepts argument "body" to process message body.
                        "stop_event" (optional): Instance of threading.Event() for stopping consuming external.
                                        If None, consume once.
        :return:
        """
        assert 'queue' in kwargs or ('topic' in kwargs and 'key' in kwargs)
        self._stop_flag = False
        queue = kwargs['queue'] if 'queue' in kwargs else None
        topic = kwargs['topic'] if 'topic' in kwargs else None
        key = kwargs['key'] if 'key' in kwargs else None
        callback = kwargs['callback'] if 'callback' in kwargs else lambda x: log.debug('Received message:  %s' % x)
        stop_event = kwargs['stop_event'] if 'stop_event' in kwargs else None

        channel = self.channel
        queue_name = queue
        if queue:
            channel.queue_declare(queue=queue_name, durable=True)
            log.debug('consuming queue %s' % queue_name)
        else:
            channel.exchange_declare(exchange=topic, type='topic')
            result = channel.queue_declare(exclusive=True)
            queue_name = result.method.queue
            channel.queue_bind(exchange=topic,
                               queue=queue_name,
                               routing_key=key)
            log.debug('consuming exchange (topic "%s" key "%s") queue %s' % (topic, key, queue_name))

        while True:
            method, properties, body = channel.basic_get(queue=queue_name, no_ack=True)
            if body:
                callback(body)
            if stop_event is None or stop_event.isSet():
                break
            sleep(1)

    def stop(self):
        """
        Stop consuming
        :return:
        """
        self._stop_flag = True