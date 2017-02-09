#!/usr/bin/env python
# coding: utf-8

"""
Some base mixins for tests
"""

from pyqueuer.models import UserConf
from pyqueuer.consts import ConfKeys


class MQTestMixin():

    @staticmethod
    def guess_mq_type(user):
        ucf = UserConf(user=user)
        for section, confkeys in ConfKeys.items():
            if section == 'General':
                continue

            v = ucf.get(confkeys.host)
            if v:
                return section

        raise Exception('You must specify at least one MQ setting.')

    def get_arguments(self,mq_type):
        return {}