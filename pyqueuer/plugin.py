#!/usr/bin/env python
# coding: utf-8
__author__ = 'Samuel Chen <samuel.net@gmail.com>'
__date__ = '12/9/2016 2:25 PM'

'''
plugin module description

Created on 12/9/2016
'''
import abc
import importlib
from yapsy.PluginManager import PluginManager
from yapsy.PluginFileLocator import PluginFileAnalyzerMathingRegex
import re
from collections import OrderedDict
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


class MessageAutoUpdater(PluginBase):
    """
    Plugin to automatically update a message without new value.
    New value will be automatically generated.
    """
    __metaclass__ = abc.ABCMeta

    _key = None

    @abc.abstractmethod
    def update(self, message):
        pass

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        self._key = value

    @property
    def is_auto_value(self):
        return True


class MessageUpdater(PluginBase):
    """
    Plugin to update a message with given new value.
    """
    __metaclass__ = abc.ABCMeta

    _key = None

    @abc.abstractmethod
    def update(self, message, value):
        pass

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        self._key = value

    @property
    def is_auto_value(self):
        return False


class PluginFileAnalyzerMathingRegexWithInfoProperty(PluginFileAnalyzerMathingRegex):
    """
    An analyzer that targets plugins decribed by files whose name match a given regex.
    And obtain PluginInfo from module properties.
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

    @classmethod
    def __get_mgr(cls):
        if not cls.__plugin_mgr:
            analyzer = PluginFileAnalyzerMathingRegexWithInfoProperty('file_name_analyzer', r'^.*\.py$')
            mgr = PluginManager(categories_filter={
                'AutoUpdaters': MessageAutoUpdater,
                'Updaters': MessageUpdater
            })
            mgr.setPluginPlaces(["plugins"])
            mgr.getPluginLocator().removeAllAnalyzer()
            mgr.getPluginLocator().appendAnalyzer(analyzer)
            mgr.locatePlugins()
            mgr.loadPlugins()
            cls.__plugin_mgr = mgr

        return cls.__plugin_mgr

    @classmethod
    def all(cls, category=None):
        mgr = cls.__get_mgr()
        if category:
            return mgr.getPluginsOfCategory(category)
        else:
            return mgr.getAllPlugins()

    @classmethod
    def all_metas(cls, category=None):
        plugins = OrderedDict()
        for plugin in cls.all(category=category):
            plugins[plugin.name] = PropertyDict({
                "name": plugin.name,
                "author": plugin.author,
                "version": plugin.version,
                "description": plugin.description,
                "plugin_object": plugin.plugin_object,

                "checked": False,
                "key": plugin.plugin_object.key,
                "value": None,
            })
        return plugins


__all__ = [
    MessageUpdater,
    MessageAutoUpdater,
    Plugins,
]