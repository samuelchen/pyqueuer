#!/usr/bin/env python
# coding: utf-8

"""
A service for pyqueuer demo (use case 1).
"""

import pika
import configparser
from time import sleep
import re
import datetime
import simplejson as json
from collections import namedtuple


# class LogEntry(object):
# level = 'NOTSET'
#     timestamp = ''
#     module = ''
#     line = -1
#     message = ''
#
#     def __repr__(self):
#         return '{"level": "%s", "timestamp": "%s", "module": "%s", "line": %d, "message": "%s"}' % (
#             self.level, self.timestamp, self.module, self.line, self.message
#         )


LogEntry = namedtuple('LogEntry', ['level', 'timestamp', 'module', 'line', 'message'])


class LogService(object):
    _regx = re.compile(r'\s+')

    def __init__(self):
        self.cf = configparser.ConfigParser()
        self.cf.read('case1.ini')
        self._conn = None
        self._queue = 'logs'
        self._topic = 'logs'
        self._flag = False  # flag for stopping

    @property
    def connection(self):
        if self._conn is None or not self._conn.is_open:
            host = self.cf.get('rabbit', 'host')
            port = int(self.cf.get('rabbit', 'port'))
            vhost = self.cf.get('rabbit', 'vhost')
            user = self.cf.get('rabbit', 'user')
            pwd = self.cf.get('rabbit', 'password')
            # print(host, port, vhost, user, pwd)

            cred = pika.PlainCredentials(username=user, password=pwd)
            parms = pika.ConnectionParameters(host=host, port=port, virtual_host=vhost, credentials=cred)
            self._conn = pika.BlockingConnection(parameters=parms)
            print('Connected.')
        return self._conn

    def start(self):
        print('> Start consuming ...')
        try:
            channel = self.connection.channel()
            channel.queue_declare(queue=self._queue, durable=False)
            while True:
                if self._flag:
                    break
                try:
                    method, properties, body = channel.basic_get(queue=self._queue, no_ack=True)
                    if body:
                        print('> received message. %s ' % body)
                        obj = LogService.process(str(body, encoding='utf-8'))
                        print('> Message processed: %s' % str(obj))
                        self.send(obj)
                except pika.exceptions.ChannelClosed:
                    channel = self.connection.channel()
                sleep(1)
        except KeyboardInterrupt:
            print('> CTRL+C pressed.')
        print('> Stopped.')

    def stop(self):
        self._flag = True

    def send(self, log_obj):
        print('> Sending message ...')
        channel = self.connection.channel()
        # channel.exchange_declare(exchange=self._topic, type='topic')
        # result = channel.queue_declare(exclusive=True)
        # queue = result.method.queue
        # channel.queue_bind(exchange=self._topic,
        # queue_name=queue,
        #                    routing_key=log_obj.level)
        msg = json.dumps(log_obj)
        print(msg)
        channel.basic_publish(exchange=self._topic,
                              routing_key=log_obj.level,
                              body=msg,
                              properties=pika.BasicProperties(
                                  content_type='application/json',
                                  delivery_mode=2))
        print('> Message sent.')


    @staticmethod
    def process(log_str):
        # log format is %(levelname)-8s [%(asctime)s] %(name)-30s [%(lineno)d] %(message)s

        matches = LogService._regx.split(string=log_str, maxsplit=5)
        log = LogEntry(
            level=matches[0].lower(),
            # timestamp=datetime.datetime.strptime(
            #     '%s %s' % (matches[1][1:], matches[2][:-1]),
            #     '%Y-%m-%d %H:%M:%S,%f'
            # ),
            timestamp='%s %s' % (matches[1][1:], matches[2][:-1]),
            module=matches[3],
            line=int(matches[4][1:-1]),
            message=matches[5]
        )
        return log


if __name__ == '__main__':
    svc = LogService()
    svc.start()