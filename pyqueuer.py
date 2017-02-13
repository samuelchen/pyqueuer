#!/usr/bin/env python
import os
import sys
import django.core.management
from django.core.management import lru_cache, find_commands, apps
from django.conf import settings

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
        if not app_config.label.startswith('pyqueuer'):
            continue
        path = os.path.join(app_config.path, 'management')
        commands.update({name: app_config.name for name in find_commands(path)})

    return commands

save_get_commands = django.core.management.get_commands
django.core.management.get_commands = get_commands


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pyqueuer.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

django.core.management.get_commands = save_get_commands
