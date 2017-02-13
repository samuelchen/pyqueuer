#!/usr/bin/env python
# coding: utf-8

"""
Some base mixins for tests
"""

from pyqueuer.models import UserConf
from pyqueuer.consts import ConfKeys
from pyqueuer.consts import MQTypes


class MQTestMixin():

    @staticmethod
    def guess_mq_type(user):
        mqtypes = []
        ucf = UserConf(user=user)
        for section, confkeys in ConfKeys.items():
            if section == 'General':
                continue

            v = ucf.get(confkeys.host)
            if v:
                mqtypes.append(section)

        if len(mqtypes) > 0:
            return mqtypes
        else:
            raise Exception('You must specify at least one MQ setting.')
