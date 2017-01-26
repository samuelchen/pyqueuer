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
import sys


class Command(BaseCommand):

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
            help='Admin password.',
        )

        parser.add_argument(
            '--email', '-m',
            action='store',
            type=str,
            dest='email',
            default='anonymous@localhost.localdomain',
            help='Admin user email.',
        )

        parser.add_argument(
            '--tester', '-t',
            action='store_true',
            dest='tester',
            default=False,
            help='Initialize a tester user.',
        )

        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            dest='quiet',
            default=False,
            help='Quiet mode. Answer "YES" for all critical question. Use RANDOM password.',
        )

    def handle(self, *args, **options):

        # initialize database
        user = options['user']
        pwd = options['password']
        email = options['email']
        tester = options['tester']
        quiet = options['quiet']

        if quiet:
            if not pwd:
                sys.stderr.write('You must specify --password argument if --quiet enabled.\r\n')
                return

        print('Initialize Database ...')
        rt = call_command(makemigrations.Command(), 'pyqueuer')
        rt = call_command(migrate.Command())

        print('Creating Admin user "%s" ...' % user)
        try:
            if quiet or pwd:
                rt = call_command(createsuperuser.Command(), '--noinput', username=user, email=email)
                u = User.objects.get(username__exact=user)
                u.set_password(raw_password=pwd)
                u.save()
            else:
                rt = call_command(createsuperuser.Command(), username=user, email=email)

        except IntegrityError:
            sys.stderr.write('  Admin with same name is already existed.\r\n')
        else:
            print('  Admin user "%s" created. Email is "%s"' % (user, email))

        if tester:
            print('Creating tester user ...')
            try:
                u = User.objects.create(username='tester')
                u.email = 'tester@localhost.localdomain'
                u.set_password(raw_password='tester')
                u.is_active = True
                u.save()
            except IntegrityError:
                sys.stderr.write('  Tester is already existed.\r\n')
            else:
                print('  Tester is created.')

