#!/usr/bin/env python
# coding: utf-8
from django.core.management.base import BaseCommand
from ...utils import Utils
import sys


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('config_file', nargs='?', type=str, help='CA Handler config file full path.')

    def handle(self, *args, **options):

        if options['config_file']:
            config_file = options['config_file']
            Utils.import_config(config_file)
        else:
            sys.stderr.write('[Error] You must specify the config file.')

