#!/usr/bin/env python
# coding: utf-8

"""
customer tags for template
"""

from django.template import Library
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
import re

register = Library()


@stringfilter
def spacify(value, autoescape=None):
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    return mark_safe(re.sub('\s', '&' + 'nbsp;', esc(value)))

@stringfilter
def _2space(value):
    """
    Convert underscores to spaces for a string.
    :param value:
    :return:
    """
    return value.replace('_', ' ')

@stringfilter
def space2_(value):
    """
    Convert spaces to underscores for a string.
    :param value:
    :return:
    """
    return value.replace(' ', '_')

spacify.needs_autoescape = True
register.filter(spacify)
register.filter(_2space)
register.filter(space2_)