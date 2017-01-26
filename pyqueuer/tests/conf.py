#!/usr/bin/env python
# coding: utf-8

"""
Some configurations for testing
"""

from pyqueuer.utils import PropertyDict

conf_tester = PropertyDict(
    user="test",
    password="test"
)

conf_rabbit = PropertyDict(
    host="192.168.0.93",
    port=5672,
    user="test",
    password="test",
    vhost="/test",
    queue_out="test",
    topic_out="test",
    key_out="test",
)