#!/usr/bin/env python
# coding: utf-8

"""
mq modules defines Message Queue clients and some tools.

"""

from ..utils import PropertyDict
from .rabbit import RabbitMQConnection
from .kafka import KafkaConnection
from ..models import UserConf
from .base import MQException, MQAuthorizeException, MQConnectException
from ..consts import MQTypes, RabbitConfKeys, KafkaConfKeys


class MQClientFactory():

    def __init__(self, mq_type):
        self._mq_type = mq_type
        if mq_type not in MQTypes.values:
            raise RuntimeError('Unsupported MQ type "%s"' % mq_type)

    @staticmethod
    def create_connection(mq_type, conf):
        """
        A factory for MQ Connection
        :param mq_type: Message queue type from MQTypes
        :param conf: The configuration dict
        :return:
        """
        conn = None
        if mq_type == MQTypes.RabbitMQ:
            conn = RabbitMQConnection(conf)
        elif mq_type == MQTypes.Kafka:
            conn = KafkaConnection(conf)
        else:
            raise RuntimeError('Unsupported MQ type "%s"' % mq_type)

        # assign methods
        conn.mq_type = mq_type
        # conn.create_producer = MQClientFactory.__create_producer
        # conn.create_consumer = MQClientFactory.__create_consumer
        return conn

    @staticmethod
    def create_producer(mq_type, conf):
        """
        Create a MQ producer instance.
        :param mq_type:
        :param conf:
        :return:
        """
        conn = MQClientFactory.create_connection(mq_type, conf)
        producer = conn.create_producer()
        return producer

    @staticmethod
    def create_consumer(mq_type, conf):
        """
        Create a MQ consumer instance.
        :param mq_type:
        :param conf:
        :return:
        """
        conn = MQClientFactory.create_connection(mq_type, conf)
        producer = conn.create_consumer()
        return producer

    # @staticmethod
    # def __create_producer(conn):
    #     mq_type = conn.mq_type
    #     if mq_type == MQTypes.RabbitMQ:
    #         return RabbitMQProducer(conn)
    #     elif mq_type == MQTypes.Kafka:
    #         return KafkaProducer(conn)
    #     else:
    #         raise RuntimeError('Unsupported MQ type "%s"' % mq_type)
    #
    # @staticmethod
    # def __create_consumer(conn):
    #     mq_type = conn.mq_type
    #     if mq_type == MQTypes.RabbitMQ:
    #         return RabbitMQConsumer(conn)
    #     elif mq_type == MQTypes.Kafka:
    #         return KafkaConsumer(conn)
    #     else:
    #         raise RuntimeError('Unsupported MQ type "%s"' % mq_type)

    @staticmethod
    def get_confs(mq_type, user):
        """
        Retrieve mq configurations of a user based on MQ type
        :param mq_type:
        :param user:
        :return: PropertyDict
        """
        ucfg = UserConf(user=user)

        conf_keys = None
        if mq_type == MQTypes.RabbitMQ:
            conf_keys = RabbitConfKeys
        elif mq_type == MQTypes.Kafka:
            conf_keys = KafkaConfKeys
        else:
            raise RuntimeError('Unsupported MQ type "%s"' % mq_type)

        confs = PropertyDict.fromkeys(conf_keys.values())
        for value in conf_keys.values():
            confs[value] = ucfg.get(value)
        return confs


__all__ = [
    MQTypes,
    MQClientFactory,
    MQException, MQAuthorizeException, MQConnectException,
]