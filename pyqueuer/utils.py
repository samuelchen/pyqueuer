#!/usr/bin/env python
# coding: utf-8
__author__ = 'Samuel Chen <samuel.net@gmail.com>'
__date__ = '10/27/2016 5:37 PM'

'''
utils module description

Created on 10/27/2016
'''
import collections
import simplejson as json
import uuid
import datetime
import pathlib
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


def update_message(json_str, auto_uuid=False, auto_time=True, timeout=-1):

    if not (auto_uuid or auto_time or timeout > 0):
        return json_str

    item = json.loads(json_str)
    if auto_uuid:
        item['uuid'] = str(uuid.uuid4())
    if auto_time:
        item['create_time'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
    if timeout > 0:
        item['time_out'] = timeout * 1000  # s -> ms
    rc = json.dumps(item)
    return rc


from yapsy.PluginManager import PluginManager
from yapsy.PluginFileLocator import PluginFileAnalyzerMathingRegex
from pyqueuer.plugin import MessageAutoUpdater, MessageUpdater, Plugins


def up_message(msg, plugin_names):
    mgr = Plugins

    for plugin in mgr.all('AutoUpdaters'):
        try:
            print(plugin.name, plugin)
            msg = plugin.plugin_object.update(msg)
        except Exception as err:
            log.exception(err)

    values = {
        'json_timeout_updater': ('time_out', 10)
    }
    for plugin in mgr.all('Updaters'):
        try:
            print(plugin.name, plugin)
            k, v = values[plugin.name]
            plugin.plugin_object.key = k
            msg = plugin.plugin_object.update(msg, v)
        except Exception as err:
            log.exception(err)

    return msg


if __name__ == '__main__':
    print(up_message('{"uuid": "123", "time_out": "99", "create_time": "2016-12-01Z18:23:43.343"}', ['sample_json']))