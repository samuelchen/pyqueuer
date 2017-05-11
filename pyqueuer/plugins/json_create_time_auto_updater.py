#!/usr/bin/env python
# coding: utf-8

"""
Sample for updating json fields.
"""

import simplejson as json
import datetime
from pyqueuer.plugin import IndividualUpdater


class CreateTimeAutoUpdater(IndividualUpdater):
    def update(self, message, arguments):
        obj = json.loads(message)
        if 'create_time' in obj:
            obj['create_time'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
            message = json.dumps(obj)
        return message


# meta info for plugin
Name = 'Auto-CreateTime'
Author = 'Samuel'
Version = '1.0.0'
Website = 'http://samuelchen.net'
Description = 'Automatically update "create_time" field in a JSON message.'
Copyright = 'FreeBSD'
