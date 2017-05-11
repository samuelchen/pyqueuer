#!/usr/bin/env python
# coding: utf-8

"""
Command line initialization.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.core.management.commands import migrate, makemigrations
from django.contrib.auth.management.commands import createsuperuser
from django.db.utils import IntegrityError
from django.contrib.auth.models import User
from django.conf import settings
import sys
import os
from ...consts import ConfKeys


class Command(BaseCommand):

    default_tester_config = os.path.sep.join([settings.BASE_DIR, 'tester_config.ini'])

    def add_arguments(self, parser):

        parser.add_argument(
            '--user', '-u',
            action='store',
            type=str,
            dest='user',
            default='admin',
            help='Admin user name. Default is "admin".',
        )

        parser.add_argument(
            '--password', '-p',
            action='store',
            type=str,
            dest='password',
            help='Admin password. If not specified, will prompt to enter.',
        )

        parser.add_argument(
            '--email', '-m',
            action='store',
            type=str,
            dest='email',
            default='anonymous@localhost',
            help='Admin user email.',
        )

        parser.add_argument(
            '--tester', '-t',
            action='store_true',
            dest='tester',
            default=False,
            help='Initialize a tester user. Username and password are both "%s" (settings.TESTER).' % settings.TESTER,
        )

        parser.add_argument(
            '--config-file', '-f',
            action='store',
            type=str,
            dest='config_file',
            default=Command.default_tester_config,
            help='Specify tester configuration file to be imported while creating tester.'
                 'Default is "tester_config.ini" in "%s". Must with --tester=True.' % settings.BASE_DIR
        )

        parser.add_argument(
            '--create-tester-config', '-c',
            action='store_true',
            dest='create_tester_config',
            default=False,
            help='Create tester configuration file.'
        )

    def handle(self, *args, **options):

        # initialize database
        user = options['user']
        pwd = options['password']
        email = options['email']
        tester = options['tester']
        tester_config = options['config_file']
        create_tester_config = options['create_tester_config']

        # Create tester config will return immediately without init db
        if create_tester_config:
            with open(tester_config, 'wt') as f:
                f.write(os.linesep.join(['# Tester configurations (tester is set in settings.py).',
                                         '# Update me before run auto-unittests.',
                                         '# Unittest will select the configured MQ to perform tests on.']))
                for section, confs in ConfKeys.items():
                    for k, v in confs.items():
                        f.write('%s= %s' % (v, os.linesep))
            return 'Tester configuration file is created at %s' % tester_config

        # init db & migrate
        print('Initialize Database ...')
        call_command(makemigrations.Command(), 'pyqueuer')
        call_command(migrate.Command())

        # create admin
        print('Creating admin user "%s" ...' % user)
        try:
            if pwd:
                call_command(createsuperuser.Command(), '--noinput', username=user, email=email)
                u = User.objects.get(username__exact=user)
                u.set_password(raw_password=pwd)
                u.save()
            else:
                call_command(createsuperuser.Command(), username=user, email=email)

        except IntegrityError:
            sys.stderr.write('  Admin with same name is already existed.' + os.linesep)
        else:
            print('  Admin user "%s" created. Email is "%s"' % (user, email))

        # create tester
        if tester:
            name = pwd = settings.TESTER
            print('Creating test user "%s"...' % name)
            try:
                u = User.objects.create(username=name)
                u.email = email
                u.set_password(raw_password=pwd)
                u.is_active = True
                u.save()
            except IntegrityError:
                sys.stderr.write('  Tester is already existed.' + os.linesep)
            else:
                print('  Tester is created. Username and password are both "%s".' % name)

            # load tester configurations from tester json
            # Use "manage.py config --import my_config.ini" to import config only.
            if tester_config:
                print('Load config for tester.')
                options = {
                    "import": tester_config,
                    "config_file": tester_config,
                    "user": settings.TESTER,
                    "password": settings.TESTER
                }
                call_command('config', **options)
            # with open(tester_config, 'rt') as f:
            #     tester_dict = json.load(f)
            #
            # user = authenticate(username=name, password=pwd)
            # ucf = UserConf(user=user)
            # for k, v in tester_dict['test_user_config'].items():
            #     ucf.set(k, v)
            # return 'Tester configuration loaded from json %s' % tester_config

        return
