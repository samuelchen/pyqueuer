#!/usr/bin/env python
# coding: utf-8
from django.core.management.base import BaseCommand
from ... import models
from ...utils import Utils


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--file', '-f',
            action='store',
            type=str,
            dest='file',
            default='',
            help='The file to load data from.',
        )
        parser.add_argument(
            '--json', '-j',
            action='store',
            type=str,
            dest='json',
            default='',
            help='The json data to be sent.',
        )
        parser.add_argument(
            '--data', '-d',
            action='store',
            type=str,
            dest='data',
            default='',
            help='The raw text data to be sent.',
        )
        parser.add_argument(
            '--exchange', '-e',
            action='store',
            type=str,
            dest='exchange',
            default=models.Setting.get(name='rabbitmq_exchange_in'),
            help='The exchange to consume from',
        )
        parser.add_argument(
            '--key', '-k',
            action='store',
            type=str,
            dest='key',
            default=models.Setting.get(name='rabbitmq_key'),
            help='The binding key for consuming from a exchange. Only available when exchange specified',
        )
        parser.add_argument(
            '--queue', '-q',
            action='store',
            type=str,
            dest='queue',
            default=models.Setting.get(name='rabbitmq_queue_out'),
            help='The queue to send to. If exchange and key specified, queue will be ignored.',
        )

    def handle(self, *args, **options):
        # Utils.set_output(self.stdout, self.stderr)

        json = options['json']
        file = options['file']
        data = options['data']

        msg = ''
        if data:
            msg = data
        elif json:
            msg = json
        elif file:
            with open(file) as f:
                msg = f.read()

        exchange = options['exchange']
        key = options['key']
        queue = options['queue']
        Utils.send(content=msg, exchange=exchange, key=key, queue=queue)

        # Utils.reset_output()

