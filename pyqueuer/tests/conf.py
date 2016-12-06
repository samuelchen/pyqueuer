#!/usr/bin/env python
# coding: utf-8
__author__ = 'Samuel Chen <samuel.net@gmail.com>'
__date__ = '11/9/2016 2:16 PM'

'''
conf module description

Created on 11/9/2016
'''
from pyqueuer.utils import PropertyDict

conf_rabbit = PropertyDict(
    host="192.168.0.93",
    port=5672,
    user="rm",
    password="rm",
    vhost="/test"
)