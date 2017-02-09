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
from django.contrib.auth import authenticate
from django.conf import settings
import sys
import os
import simplejson as json
import tempfile
from ...utils import PropertyDict
from ...consts import MQTypes, GeneralConfKeys, RabbitConfKeys, KafkaConfKeys
from ...models import UserConf


# Preparation Data
#   admin_password: Used to initialize test database. Ignore it in most cases.
#   mq_type: Select which MQ to performing tests on. Check MQTypes.
#   test_user_config: The configurations for tester. Config it in test.json before test.
#   "RabbitMQ/Kafka/...": (generated from MQTypes) Arguments for for test.
#                           Will be used in test depends on your "mq_type".
prepare_data = PropertyDict((
    ("test_user_config", PropertyDict((
        (GeneralConfKeys.data_store, os.path.sep.join([tempfile.gettempdir(), 'data_store'])),
        (GeneralConfKeys.result_store, os.path.sep.join([tempfile.gettempdir(), 'result_store'])),

        (RabbitConfKeys.host, ""),
        (RabbitConfKeys.port, 5672),
        (RabbitConfKeys.user, ""),
        (RabbitConfKeys.password, ""),
        (RabbitConfKeys.vhost, ""),
        (RabbitConfKeys.queue_in, ""),
        (RabbitConfKeys.topic_in, ""),
        (RabbitConfKeys.key_in, ""),
        (RabbitConfKeys.queue_out, ""),
        (RabbitConfKeys.topic_out, ""),
        (RabbitConfKeys.key_out, ""),

        (KafkaConfKeys.host, ""),
        (KafkaConfKeys.port, "9092"),
        (KafkaConfKeys.topic_in, ""),
        (KafkaConfKeys.topic_out, ""),
    ))),
))  # use PropertyDict( tuple ) to keep order.


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
            '--tester_json', '-j',
            action='store',
            type=str,
            dest='tester_json',
            default=os.path.sep.join([settings.BASE_DIR, 'tester.json']),
            help='Specify user configuration json file. Default is "tester.json" in "%s".' % settings.BASE_DIR
        )

        parser.add_argument(
            '--create_tester_json', '-c',
            action='store_true',
            dest='create_tester_json',
            default=False,
            help='Create user configuration json file for tester.'
        )

    def handle(self, *args, **options):

        # initialize database
        user = options['user']
        pwd = options['password']
        email = options['email']
        tester = options['tester']
        tester_json = options['tester_json']
        create_tester_json = options['create_tester_json']

        # Create tester json will return immediately without init db
        if create_tester_json:
            with open(tester_json, 'wt') as f:
                json.dump(prepare_data, f, indent=4)
            return 'Tester configuration json file is created at %s' % tester_json

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
            sys.stderr.write('  Admin with same name is already existed.' + os.path.sep)
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
                sys.stderr.write('  Tester is already existed.' + os.path.sep)
            else:
                print('  Tester is created. Username and password are both "%s".' % name)

            # load tester configurations from tester json
            name = pwd = settings.TESTER
            with open(tester_json, 'rt') as f:
                tester_dict = json.load(f)

            user = authenticate(username=name, password=pwd)
            ucf = UserConf(user=user)
            for k, v in tester_dict['test_user_config'].items():
                ucf.set(k, v)
            return 'Tester configuration loaded from json %s' % tester_json

        return
