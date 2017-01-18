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
@register.filter(needs_autoescape=True)
def spacify(value, autoescape=None):
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    return mark_safe(re.sub('\s', '&' + 'nbsp;', esc(value)))


@stringfilter
@register.filter
def _2space(value):
    """
    Convert underscores to spaces for a string.
    :param value:
    :return:
    """
    return value.replace('_', ' ')


@stringfilter
@register.filter
def space2_(value):
    """
    Convert spaces to underscores for a string.
    :param value:
    :return:
    """
    return value.replace(' ', '_')


@register.simple_tag
def key_from_var(obj, *args):
    """
    Obtain values from dict/object with given key variables in template.
    :param obj:
    :param args:
    :return:
    """
    val = obj
    for key in args:
        if key in val:
            val = val[key]
        elif hasattr(val, key):
            val = getattr(val, key)
        else:
            return ''
    return val
