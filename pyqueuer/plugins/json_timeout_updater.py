#!/usr/bin/env python
# coding: utf-8

"""
Sample for updating json fields.
"""

import simplejson as json
from pyqueuer.plugin import IndividualUpdater


class TimeoutUpdater(IndividualUpdater):

    @property
    def params(self):
        return 'seconds',

    def update(self, message, arguments):
        key = 'time_out'
        value = arguments['seconds']
        obj = json.loads(message)
        if key in obj:
            obj[key] = int(value) * 1000  # s -> ms
            message = json.dumps(obj)
        return message


# meta info for plugin
Name = 'Timeout'
Author = 'Samuel'
Version = '1.0.0'
Website = 'http://samuelchen.net'
Description = 'Update "time_out" field with given value in JSON message.'
Copyright = 'FreeBSD'
