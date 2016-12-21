#!/usr/bin/env python
# coding: utf-8

"""
Sample for updating json fields.

Created on 12/7/2016
"""

import simplejson as json
import uuid
from pyqueuer.plugin import MessageAutoUpdater


class UUIDAutoUpdater(MessageAutoUpdater):
    def update(self, message):
        obj = json.loads(message)
        if 'uuid' in obj:
            obj['uuid'] = str(uuid.uuid4())
            message = json.dumps(obj)
        return message


# meta info for plugin
Name = 'Auto-UUID'
Author = 'Samuel'
Version = '1.0.0'
Website = 'http://samuelchen.net'
Description = 'Automatically generate & update "uuid" field in JSON message.'
Copyright = 'FreeBSD'