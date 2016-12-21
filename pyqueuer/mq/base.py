#!/usr/bin/env python
# coding: utf-8

"""
Message Queue base modules
"""

import abc
from ..utils import PropertyDict


class MQClient(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, conf, *args, **kwargs):
        """
        ctor with given configuration dict.
        :param conf: configuration dict.
        """
        self.__config = PropertyDict(conf)
        self.init(*args, **kwargs)

    @abc.abstractmethod
    def init(self, *args, **kwargs):
        """
        Abstract initialization method for children class.
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
    def reconnect(self):
        pass

    @abc.abstractmethod
    def disconnect(self):
        pass

    # ------------------------
    # Basic methods
    # ------------------------

    @abc.abstractmethod
    def basic_get(self, queue):
        pass

    @abc.abstractmethod
    def basic_send(self, message, queue):
        pass

    @abc.abstractmethod
    def basic_ack(self):
        pass

    # ------------------------
    # High level methods
    # ------------------------

    @abc.abstractmethod
    def produce(self, message):
        pass

    @abc.abstractmethod
    def consume(self):
        pass

    @abc.abstractmethod
    def produce_ex(self):
        pass

    @abc.abstractmethod
    def consume_ex(self):
        pass
