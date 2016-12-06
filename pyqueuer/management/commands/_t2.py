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

        cwd = os.getcwd()
        pwd = os.path.abspath(os.path.sep.join([os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '']))
        print('change to:', pwd)

        virtualenv = models.Setting.get('virtualenv')
        venv = ''
        if virtualenv:
            sb = [virtualenv, sys.platform.startswith('win') and 'scripts' or 'bin', 'activate_this.py']
            venv = os.path.abspath(os.path.sep.join(sb))
            venv = 'python ' + venv

        if sys.platform.startswith('win'):
            if virtualenv:
                sb = [virtualenv, 'scripts', 'activate.bat']
                venv = os.path.abspath(os.path.sep.join(sb))
            line_break = '\r\n'
            tmp = tempfile.NamedTemporaryFile(suffix='.bat', mode='w+t', delete=False)
            tmp.writelines(['@echo off', line_break])
            exe = None
        else:
            if virtualenv:
                sb = [virtualenv, 'bin', 'activate']
                venv = os.path.abspath(os.path.sep.join(sb))
                venv = 'bin ' + venv
            line_break = '\n'
            tmp = tempfile.NamedTemporaryFile(suffix='.sh', mode='w+t', delete=False)
            tmp.writelines(['#!/bin/sh', line_break])
            exe = '/bin/sh'

        cmd = ' '.join(options['cmd'])
        print(tmp.name)
        print(venv)
        print(cmd)
        if virtualenv:
            tmp.writelines([venv, line_break])
        tmp.writelines(['cd', ' ', pwd, line_break])
        tmp.writelines(['python manage.py %s' % cmd, line_break])
        #tmp.close()

        arguments = [tmp.name, ]

        p = Popen(arguments, executable=exe, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell=True)

        while p.poll() is None:
            p.stdout.flush()
            p.stderr.flush()
            print(p.stdout.read())
            print(p.stderr.read())
            sleep(0.1)
        print(p.returncode)

        # TODO: delete temp file

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

        self.wrapped()