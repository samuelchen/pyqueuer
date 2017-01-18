#!/usr/bin/env python
# coding: utf-8

"""
Message Queue base modules
"""

import abc
from ..utils import PropertyDict


class IConnect(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, conf):
        """
        ctor with given configuration dict.
        :param conf: configuration dict.
        """
        self.__config = PropertyDict(conf)
        self.init()

    @abc.abstractmethod
    def init(self):
        """
        Abstract initialization method for children class.
        Use self.config dict to initialize.
        """

    # ------------------------
    # Static methods
    # ------------------------
    pass

    # ------------------------
    # Properties
    # ------------------------
    __auto_reconnect = True

    @property
    def auto_reconnect(self):
        return self.__auto_reconnect

    @auto_reconnect.setter
    def auto_reconnect(self, value):
        self.__auto_reconnect = value

    __config = {}

    @property
    def config(self):
        return self.__config

    # ------------------------
    # Connection methods
    # ------------------------

    @abc.abstractmethod
    def connect(self):
        pass

    @abc.abstractmethod
    def disconnect(self):
        pass

    @abc.abstractmethod
    def create_producer(self):
        pass

    @abc.abstractmethod
    def create_consumer(self):
        pass


class IProduce(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, conn):
        """
        :param conn: A IConnect instance of same MQ type.
        :return:
        """
        self._conn = conn

    # ------------------------
    # Properties
    # ------------------------
    @property
    def connection(self):
        return self._conn

    # ------------------------
    # Basic methods
    # ------------------------

    @abc.abstractmethod
    def basic_send(self, message, **kwargs):
        pass

    # ------------------------
    # High level methods
    # ------------------------

    @abc.abstractmethod
    def produce(self, message, **kwargs):
        pass


class IConsume(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, conn):
        """
        :param conn: A IConnect instance of same MQ type.
        :return:
        """
        self._conn = conn

    # ------------------------
    # Properties
    # ------------------------
    @property
    def connection(self):
        return self._conn

    # ------------------------
    # Basic methods
    # ------------------------

    @abc.abstractmethod
    def basic_get(self, **kwargs):
        pass

    @abc.abstractmethod
    def basic_ack(self, **kwargs):
        pass

    # ------------------------
    # High level methods
    # ------------------------

    @abc.abstractmethod
    def consume(self, **kwargs):
        pass


    @abc.abstractmethod
    def stop(self):
        pass