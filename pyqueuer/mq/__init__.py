#!/usr/bin/env python
# coding: utf-8

"""
mq modules defines Message Queue clients and some tools.

"""

from ..utils import PropertyDict
from .rabbit import RabbitMQBlockingClient
from ..models import RabbitConfKeys, UserConf


MQTypes = PropertyDict(
    RabbitMQ='RabbitMQ',
    Kafka='Kafka'
)


def create_client(mq_type, conf):
    """
    A factory for MQ client
    :param mq_type: Message queue type from MQTypes
    :param conf: The configuration dict
    :return:
    """
    if mq_type == MQTypes.RabbitMQ:
        return RabbitMQBlockingClient(conf)
    else:
        raise RuntimeError('Unsupported MQ type')


def get_confs(user, mq_type):
    """
    Retrieve mq configurations of a user
    :param user:
    :param mq_type:
    :return: PropertyDict
    """
    ucfg = UserConf(user=user)
    confs = PropertyDict.fromkeys(RabbitConfKeys.values())
    for value in RabbitConfKeys.values():
        confs[value] = ucfg.get(value)
    return confs


__all__ = [
    MQTypes,
    create_client,
    get_confs,
]