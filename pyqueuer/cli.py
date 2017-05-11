#!/usr/bin/env python
import os
import sys
import django.core.management
from django.core.management import lru_cache, find_commands, apps
from django.conf import settings

lib_name = 'pyqueuer'

@lru_cache.lru_cache(maxsize=None)
def get_commands():
    """
    Returns a dictionary mapping command names to their callback applications.

    Copy from site-packages/django/core/management/__init__.py

    Override it to ignore django commands.
    """

    commands = {}

    if not settings.configured:
        return commands

    for app_config in reversed(list(apps.get_app_configs())):
        if app_config.label.startswith(lib_name):
            path = os.path.join(app_config.path, 'management')
            commands.update({name: app_config.name for name in find_commands(path)})

    return commands


def execute():
    sys.path.insert(0, os.curdir)
    if os.path.exists('settings.py'):
        s = 'settings'
    else:
        s = "%s.settings" % lib_name
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", s)

    save_get_commands = django.core.management.get_commands
    django.core.management.get_commands = get_commands

    from django.core.management import execute_from_command_line

    sys.argv[0] = lib_name  # for displaying correct command name in help. match "entry_points" in setup.py.
    execute_from_command_line(sys.argv)

    django.core.management.get_commands = save_get_commands


if __name__ == "__main__":
    execute()


