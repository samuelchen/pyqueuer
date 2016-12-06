#!/usr/bin/env python
# coding: utf-8
from django.core.management.base import BaseCommand
from ... import models
from ...utils import Utils
import threading


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--queue', '-q',
            action='store',
            type=str,
            dest='queue',
            default=models.Setting.get(name='rabbitmq_queue_out'),
            help='The queue to consume from.',
        )
        parser.add_argument(
            '--exchange', '-e',
            action='store',
            type=str,
            dest='exchange',
            default=models.Setting.get(name='rabbitmq_exchange_out'),
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

    def handle(self, *args, **options):
        event = threading.Event()

        queue = options['queue']
        exchange = options['exchange']
        key = options['key']
        try:
            Utils.consume(key=key, exchange=exchange, queue=queue, stop_event=event)
        except:
            event.set()


