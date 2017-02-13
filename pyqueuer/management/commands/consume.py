#!/usr/bin/env python
# coding: utf-8

from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate
from ...mq import MQTypes, MQClientFactory, MQException
from ...consts import ConfKeys
import getpass
from threading import Event
import simplejson as json
import datetime


class Command(BaseCommand):
    def add_arguments(self, parser):

        parser.add_argument(
            '--type', '-t',
            action='store',
            type=str,
            dest='type',
            help='The MQ type. Supports "%s".' % '", "'.join(MQTypes.values()),
        )

        parser.add_argument(
            '--password', '-p',
            action='store',
            type=str,
            dest='password',
            help='User password to login. If not specified, will prompt to enter.',
        )

        # TODO: save result (plugin or feature?)
        # parser.add_argument(
        #     '--save', '-s',
        #     action='store_true',
        #     dest='save',
        #     help='Save the incoming message to "result_store" folder.',
        # )

        parser.add_argument(
            '--user', '-u',
            action='store',
            type=str,
            dest='user',
            help='User name to login. If not specified, will prompt to enter.',
        )

        parser.add_argument(
            'arguments',
            nargs='+',
            type=str,
            metavar='arguments_for_mq',
            help='MQ arguments "queue=logs [topic=new ...]" (no space around "=").'
        )

    def handle(self, *args, **options):

        mqtype = options['type']
        name = options['user']
        pwd = options['password']
        # TODO: save = options['save']
        arguments = options['arguments']

        if not name:
            name = input('Please enter your user name:')

        if not pwd:
            pwd = getpass.getpass('Please enter the password for user "%s" :' % name)

        user = authenticate(username=name, password=pwd)
        if user and user.is_active:
            pass
        else:
            return 'You are not authorized with given user name and password.'

        if not mqtype:
            return 'You must specify MQ type.'

        kwargs = {}
        if arguments:
            for token in arguments:
                opt = token.split('=')
                if len(opt) != 2:
                    return 'Invalid syntax around "%s"' % token
                opt[0] = opt[0].strip()
                kwargs[opt[0]] = opt[1]

        def on_msg(msg):
            breaker = '-' * 20
            s = msg
            try:
                obj = json.loads(msg)
                s = json.dumps(obj, indent=2)
            except json.scanner.JSONDecodeError:
                s = msg.decode() if msg else None

            print('%s [x] %s %s' % (breaker, datetime.datetime.now(), breaker))
            print(s)

        stop_event = Event()
        kwargs['stop_event'] = stop_event
        kwargs['callback'] = on_msg

        if 'durable' in kwargs:
            kwargs['durable'] = bool(kwargs['durable'])

        confs = MQClientFactory.get_confs(mq_type=mqtype, user=user)
        client = MQClientFactory.create_consumer(mq_type=mqtype, conf=confs)
        keys = ConfKeys[mqtype]
        try:
            print('Consuming %s %s:%s %s (%s)...' % (mqtype, confs[keys.host], confs[keys.port],
                                                     confs[keys.vhost] if mqtype == MQTypes.RabbitMQ else '',
                                                     arguments))
            client.consume(**kwargs)
        except KeyboardInterrupt:
            return 'Break by CTRL+C.'
        except MQException as err:
            return str(err)

