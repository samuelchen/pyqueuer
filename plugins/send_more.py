#!/usr/bin/env python
# coding: utf-8

"""
Batch updater to send a message multiple times
"""

from pyqueuer.plugin import BatchUpdater, PluginException


class SendMore(BatchUpdater):

    @property
    def is_auto_value(self):
        return False

    def run(self, *args, **kwargs):
        if len(args) < 1:
            raise PluginException('You must specify sending count.')
        count = int(args[0])
        for i in range(0, count):
            # self.update_message(None)
            self.send()


# meta info for plugin
Name = 'Send-More'
Author = 'Samuel'
Version = '1.0.0'
Website = 'http://samuelchen.net'
Description = 'Send a message many times by given count'
Copyright = 'FreeBSD'