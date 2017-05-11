#!/usr/bin/env python
# coding: utf-8

from django.core.management import BaseCommand
from django.conf import settings
import os
import shutil

lib_name = 'pyqueuer'


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'path',
            nargs='?',
            type=str,
            metavar='path',
            default='.',
            help='Project initialization path.'
        )

    def handle(self, *args, **options):
        origin_base = settings.BASE_DIR

        path = options['path']
        cur_base = os.path.abspath(path)

        if origin_base in cur_base:
            return 'You cannot create PyQueuer project in a existing project.'

        if path != '.':
            os.makedirs(cur_base)

        # copy files
        shutil.copy(os.path.join(origin_base, lib_name, '__init__.py'), cur_base)
        shutil.copy(os.path.join(origin_base, lib_name, 'wsgi.py'), cur_base)
        # shutil.copy(os.path.join(origin_base, lib_name, 'urls.py'), cur_base)
        # shutil.copy(os.path.join(origin_base, lib_name, 'settings.py'), cur_base)

        # change setting
        with open(os.path.join(origin_base, lib_name, 'settings.py'), 'r', encoding='utf-8') as f1:
            with open(os.path.join(cur_base, 'settings.py'), 'w', encoding='utf-8') as f2:
                for line in f1.readlines():
                    if line.startswith('BASE_DIR ='):
                        line = "BASE_DIR = '%s'" % os.path.abspath(os.curdir)
                    elif line.startswith('DEBUG ='):
                        line = "DEBUG = False\n"
                    elif line.startswith('WSGI_APPLICATION ='):
                        line = "WSGI_APPLICATION = 'wsgi.application'\n"
                    f2.write(line)
