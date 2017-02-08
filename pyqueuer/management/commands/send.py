#!/usr/bin/env python
# coding: utf-8

from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate
from ...mq import MQTypes, MQClientFactory, MQException
from ...models import UserConf
from ...consts import GeneralConfKeys
import getpass
import pathlib


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
            '--file', '-f',
            action='store',
            type=str,
            dest='file',
            help='The file to load data from.',
        )

        parser.add_argument(
            '--data', '-d',
            action='store',
            type=str,
            dest='data',
            help='The raw text data to be sent.',
        )

        parser.add_argument(
            '--password', '-p',
            action='store',
            type=str,
            dest='password',
            help='User password to login. If not specified, will prompt to enter.',
        )

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
            help='MQ arguments as "queue=logs [topic=new ...]" (no space around "=").\r\n'
                 '"queue" or "topic" + "key". If all specified, accept "queue";\r\n'
                 '"content_type" (optional): Specify content type. Default is "plain/text";\r\n'
                 '"mode" (optional): Specify delivery mode. Default is 2. (Check Rabbit Doc);\r\n',
        )

    def handle(self, *args, **options):

        mqtype = options['type']
        name = options['user']
        pwd = options['password']
        arguments = options['arguments']
        file = options['file']
        data = options['data']

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

        ucf = UserConf(user=user)

        msg = ''
        if data:
            msg = data
        elif file:
            p = pathlib.Path(file)
            if not p.exists():
                p = pathlib.Path(ucf.get(GeneralConfKeys.data_store), file)
                if not p.exists():
                    return 'File is not accessible.'
            with p.open('tr') as f:
                msg = f.read()

        else:
            return 'You must specify either --data or --file for reading message.'

        kwargs = {}
        if arguments:
            for token in arguments:
                opt = token.split('=')
                if len(opt) != 2:
                    return 'Invalid syntax around "%s"' % token
                opt[0] = opt[0].strip()
                kwargs[opt[0]] = opt[1]

        confs = MQClientFactory.get_confs(mq_type=mqtype, user=user)
        client = MQClientFactory.create_producer(mq_type=mqtype, conf=confs)
        try:
            client.produce(message=msg, **kwargs)
        except KeyboardInterrupt:
            return 'Break by CTRL+C.'
        except MQException as err:
            return str(err)

        return 'Message sent.'