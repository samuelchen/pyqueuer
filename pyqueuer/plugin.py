#!/usr/bin/env python
# coding: utf-8

"""
plugin module defines the base classes for writing plugins.
This module contains some plugin management classes as well.

Created on 12/9/2016
"""

import abc
import importlib
from yapsy.PluginManager import PluginManager
from yapsy.PluginFileLocator import PluginFileAnalyzerMathingRegex
import re
from .utils import PropertyDict

re_valid_plugin_name = re.compile(r'^[a-zA-Z0-9_\-]+$')


class PluginBase(object):
    """
    Base class for all plugins
    """

    __metaclass__ = abc.ABCMeta

    _is_activated = False

    @property
    def is_activated(self):
        return self._is_activated

    @is_activated.setter
    def is_activated(self, value):
        assert isinstance(value, bool)
        self._is_activated = value

    @abc.abstractproperty
    def is_auto_value(self):
        pass


class PluginException(Exception):
    pass

# --- individual message updater ---


class Updater(PluginBase):

    __metaclass__ = abc.ABCMeta

    _key = None

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        self._key = value

    @abc.abstractproperty
    def is_auto_value(self):
        pass


class MessageAutoUpdater(Updater):
    """
    Plugin to automatically update a message without new value.
    New value will be automatically generated.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def update(self, message):
        pass

    @property
    def is_auto_value(self):
        return True


class MessageUpdater(Updater):
    """
    Plugin to update a message with given new value.
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def update(self, message, value):
        pass

    @property
    def is_auto_value(self):
        return False

# --- batch messages updater ---


class BatchUpdater(PluginBase):
    """
    BatchUpdater is a plugin for batch producing messages.
    """

    __metaclass__ = abc.ABCMeta

    __func = None
    __msg = None
    __origin_msg = None

    @abc.abstractproperty
    def is_auto_value(self):
        pass

    @abc.abstractmethod
    def run(self, *args, **kwargs):
        """
        Plugin entry point. Implement this method for you plugin logic.
        :param args:
        :param kwargs:
        :return:
        """
        pass

    @property
    def send_func(self):
        """
        The callable function used to send message.
        :return:
        """
        return self.__func

    @send_func.setter
    def send_func(self, func):
        if not callable(func):
            raise PluginException('BatchUpdater.send_func must be callable which accepts an argument of message.')

        self.__func = func

    @property
    def origin_message(self):
        return self.__origin_msg

    @origin_message.setter
    def origin_message(self, value):
        self.__origin_msg = value

    def send(self):
        """ Send the message. If message is not updated, use origin message.
        :return:
        """
        if not self.__func:
            raise PluginException('send_func is None.')
        msg = self.__msg
        if not msg:
            msg = self.__origin_msg
        self.__func(msg)

    def update_message(self, message):
        """update the message to be sent"""
        self.__msg = message


# --- management ---


class PluginFileAnalyzerMathingRegexWithInfoProperty(PluginFileAnalyzerMathingRegex):
    """
    An analyzer that targets plugins described by files whose name match a given regex.
    And obtain PluginInfo from module properties.
    This class will be used to identify what file is plugin. It will also update some
    meta information for plugins.
    Used "Plugins" manager.
    """

    def getInfosDictFromPlugin(self, dirpath, filename):
        """
        Returns the extracted plugin informations as a dictionary.
        This function ensures that "name" and "path" are provided.
        """
        infos, cf_parser = super(PluginFileAnalyzerMathingRegexWithInfoProperty,
                                 self).getInfosDictFromPlugin(dirpath, filename)

        doc_keys = ['Author', 'Version', 'Website', 'Description']
        try:
            mod = importlib.import_module('plugins.' + infos["name"])
            cf_parser.add_section("Documentation")
            if mod:
                for key in doc_keys:
                    if hasattr(mod, key):
                        value = getattr(mod, key)

                        infos[key] = value
                        cf_parser.set("Documentation", key, value)
                        # print(key, value)
                if hasattr(mod, 'Name'):
                    value = getattr(mod, 'Name')
                    if not re_valid_plugin_name.match(value):
                        raise ValueError('"%s" is not valid plugin name. '
                                         ' Only A-Z(a-z), 0-9, "_" and "-" are valid.' % value)
                    infos["name"] = value
        except ImportError:
            pass

        return infos, cf_parser


class Plugins(object):
    """
    A plugin management class for quick access.
    """

    __plugin_mgr = None
    __plugins = PropertyDict()
    __plugin_list = None
    # __metas = None

    __categories = {
        'AutoUpdaters': MessageAutoUpdater,
        'Updaters': MessageUpdater,
        'Batches': BatchUpdater,
    }

    @classmethod
    def __get_mgr(cls):
        if not cls.__plugin_mgr:
            analyzer = PluginFileAnalyzerMathingRegexWithInfoProperty('file_name_analyzer', r'^.*\.py$')
            mgr = PluginManager(categories_filter=cls.__categories)
            mgr.setPluginPlaces(["plugins"])
            mgr.getPluginLocator().removeAllAnalyzer()
            mgr.getPluginLocator().appendAnalyzer(analyzer)
            mgr.locatePlugins()
            mgr.loadPlugins()
            cls.__plugin_mgr = mgr

        return cls.__plugin_mgr

    # @classmethod
    # def _all(cls, category=None):
    #     mgr = cls.__get_mgr()
    #     if category:
    #         return mgr.getPluginsOfCategory(category)
    #     else:
    #         return mgr.getAllPlugins()

    # @classmethod
    # def all_metas(cls, category=None, refresh=False):
    #     if refresh or not cls.__metas:
    #         plugins = {}
    #         for plugin in cls.all(category=category):
    #             plugins[plugin.name] = PropertyDict({
    #                 "name": plugin.name,
    #                 "author": plugin.author,
    #                 "version": plugin.version,
    #                 "description": plugin.description,
    #                 "plugin_object": plugin.plugin_object,
    #
    #                 "checked": False,
    #                 # "key": plugin.plugin_object.key,
    #                 # "value": None,
    #             })
    #         cls.__metas = OrderedDict(sorted(plugins.items(), key=lambda x: x[0]))
    #     return cls.__metas

    @classmethod
    def __load(cls, category, refresh=False):
        if refresh or category not in cls.__plugins:
            plugins = {}
            for plugin in cls.__get_mgr().getPluginsOfCategory(category):
                plugins[plugin.name] = PropertyDict({
                    "name": plugin.name,
                    "author": plugin.author,
                    "version": plugin.version,
                    "description": plugin.description,
                    "plugin_object": plugin.plugin_object,

                    # "checked": False,
                    "category": category,
                    # "key": plugin.plugin_object.key,
                    # "value": None,
                })
            cls.__plugins[category] = PropertyDict(sorted(plugins.items(), key=lambda x: x[0]))
        return cls.__plugins[category]

    # @classmethod
    # def all_in_list(cls, refresh=False):
    #     if refresh or not cls.__plugin_list:
    #         plugins = []
    #         for plugin in cls.__get_mgr().getAllPlugins():
    #             plugins.append(PropertyDict({
    #                 "name": plugin.name,
    #                 "author": plugin.author,
    #                 "version": plugin.version,
    #                 "description": plugin.description,
    #                 "plugin_object": plugin.plugin_object,
    #
    #                 "checked": False,
    #                 # "category": category,
    #                 # "key": plugin.plugin_object.key,
    #                 # "value": None,
    #             }))
    #         cls.__plugin_list = sorted(plugins, key=lambda x: x.name)
    #     return cls.__plugin_list

    @classmethod
    def all(cls, refresh=False):
        for category in cls.__categories.keys():
            if refresh or category not in cls.__plugins:
                cls.__load(category=category, refresh=refresh)
        return cls.__plugins

    @classmethod
    def batch_updaters(cls, refresh=False):
        cls.__load(category='Batches', refresh=refresh)
        return cls.__plugins['Batches']

    @classmethod
    def individual_updaters(cls, refresh=False):
        cls.__load(category='Updaters', refresh=refresh)
        cls.__load(category='AutoUpdaters', refresh=refresh)
        updaters = {}
        updaters.update(cls.__plugins['Updaters'])
        updaters.update(cls.__plugins['AutoUpdaters'])
        updaters = PropertyDict(sorted(updaters.items(), key=lambda x: x[0]))
        return updaters

    # @classmethod
    # def updaters(cls, refresh=False):
    #     cls.__load(category='Updaters', refresh=refresh)
    #     return cls.__plugins['Updaters']

__all__ = [
    MessageUpdater,
    MessageAutoUpdater,
    Plugins,
]