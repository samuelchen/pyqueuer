#!/usr/bin/env python
# coding: utf-8
from django.core.management.base import BaseCommand
from ...utils import Utils
from ... import models

from django.core.management import call_command
from multiprocessing import Process
from functools import partial
import os, sys

from subprocess import Popen, PIPE
import tempfile
from time import sleep


class Command(BaseCommand):

    wrapped = None

    def add_arguments(self, parser):
        parser.add_argument('cmd', nargs='+', type=str, help='command and args. user quotes ("foo bar") to surround multiple args.')

    def handle(self, *args, **options):
        Utils.set_output(self.stdout, self.stderr)

        p = Process(target=self.go)
        self.proc = p
        p.start()

        Utils.reset_output()

    def create_temp_file(self):
        sb = []
        if sys.platform.startswith('win'):
            sb = [models.Setting.get('virtualenv'), 'scripts', 'activate.bat']
            venv = os.path.abspath(os.path.sep.join(sb))
        else:
            sb = [models.Setting.get('virtualenv'), 'bin', 'activate']
            venv = 'source ' + os.path.abspath(os.path.sep.join(sb))

        print(venv)



    def go(self):
        activate_this = os.path.sep.join([models.Setting.get('virtualenv'), sys.platform.startswith('win') and 'script' or 'bin', 'activate_this.py'])
        #activate_this = '/path/to/env/bin/activate_this.py'
        print(activate_this)
        execfile(activate_this, dict(__file__=activate_this))
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ca_utils.settings")
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        print(sys.path)

        Utils.consume()