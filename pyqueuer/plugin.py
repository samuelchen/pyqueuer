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
        assert value is bool
        self._is_activated = value


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
                    if '--' in value:
                        raise ValueError('"--" is not allowed for plugin "Name".')
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


__all__ = [
    MessageUpdater,
    MessageAutoUpdater,
    Plugins,
]