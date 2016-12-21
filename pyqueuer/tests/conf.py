#!/usr/bin/env python
# coding: utf-8

"""
Some configurations for testing
"""

from pyqueuer.utils import PropertyDict

conf_rabbit = PropertyDict(
    host="192.168.0.93",
    port=5672,
    user="rm",
    password="rm",
    vhost="/test"
)