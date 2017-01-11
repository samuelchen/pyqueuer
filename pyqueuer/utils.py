#!/usr/bin/env python
# coding: utf-8

"""
utils module defines some convenience classes or functions.

Created on 10/27/2016
"""

import collections
import datetime
import logging
log = logging.getLogger(__name__)


class PropertyDict(collections.OrderedDict):
    """
    A class based ordered dict and supports dot notation.
    e.g. Either "obj.name" or "obj['name']" works
    """

    # def __getitem__(self, key):
    #     if self.fail_as_none and key not in self.keys():
    #         return None
    #     return super(PropertyDict, self).__getitem__(key)

    def __getattr__(self, key):
        if key in self.keys():
            return self[key]
        else:
            return super(PropertyDict, self).__getattribute__(key)

    def __setattr__(self, key, value):
        if key in self.keys():
            return super(PropertyDict, self).__setitem__(key, value)
        else:
            return super(PropertyDict, self).__setattr__(key, value)

    def __delattr__(self, key):
        if key in self.keys():
            return super(PropertyDict, self).__delitem__(key)
        else:
            return super(PropertyDict, self).__delattr__(key)

    # __fail_as_none = False
    #
    # @property
    # def fail_as_none(self):
    #     return self.__fail_as_none
    #
    # @fail_as_none.setter
    # def fail_as_none(self, value):
    #     assert value is bool
    #     self.__fail_as_none = value


# TODO: OutputBuffer should be thread-safe (is dequeue thread safe?).
class OutputBuffer(object):
    """
    OutputBuffer class is a file like class to output MQ Messages.

    """
    def __init__(self, maxlen=100):
        """
        ctor
        :param maxlen: max buffered records (lines, strings and etc.)
        :return:
        """
        self._queue = collections.deque(maxlen=maxlen)

    def __len__(self):
        return len(self._queue)

    def _write(self, message):
        msg = (message, datetime.datetime.utcnow(), )
        if self.full():
            self._queue.popleft()
        self._queue.append(msg)

    def write(self, message):
        self._write(message)

    def writelines(self, lines):
        for line in lines:
            self._write(line)

    def flush(self):
        messages = []
        for msg in self._queue:
            message, tm = msg
            messages.insert(0, {
                "message": message,
                "time": str(tm),
            })
        return messages

    def full(self):
        return len(self._queue) >= self._queue.maxlen

    def empty(self):
        return len(self._queue) <= 0
