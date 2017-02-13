#!/usr/bin/env python
# coding: utf-8

"""
models module defines the Django ORM models.
this module contains some constants as well.
"""

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from .consts import ConfKeys


class BaseModel(models.Model):
    user = models.ForeignKey(User if not hasattr(settings, 'AUTH_USER_MODEL') else settings.AUTH_USER_MODEL)

    class Meta:
        abstract = True


class Config(BaseModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    value = models.TextField()

    class Meta:
        unique_together = ('user', 'name')


class PluginStackModel(BaseModel):
    id = models.AutoField(primary_key=True)
    stack = models.CharField(max_length=250)
    plugin = models.CharField(max_length=250)
    desc = models.TextField()

    class Meta:
        unique_together = ('user', 'stack', 'plugin')


# ---------- Utils -----------------

class UserConf(object):
    """
    The utility class for accessing user configuration.
    """

    _user = None

    def __init__(self, user):
        self._user = user
        if len(self.all()) < ConfKeys.key_count:
            self.initialize()

    def initialize(self):
        for section, conf in ConfKeys.items():
            for k, v in conf.items():
                obj, created = Config.objects.get_or_create(name=v, user=self._user)
                if created:
                    obj.value = ''
                    obj.save()

    def get(self, name):
        return Config.objects.get(name=name, user=self._user).value

    def set(self, name, value):
        obj, created = Config.objects.get_or_create(name=name, user=self._user)
        obj.value = value
        obj.save()

    def all(self):
        return Config.objects.filter(user=self._user)
