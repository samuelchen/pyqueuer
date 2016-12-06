#!/usr/bin/env python
# coding: utf-8

import threading
from abc import ABCMeta
from collections import deque
import datetime
import simplejson as json
import os

from .models import UserConf, GeneralConfKeys

import logging
log = logging.getLogger(__name__)


class OutputBuffer(object):

    def __init__(self, maxlen=100):
        self._queue = deque(maxlen=maxlen)     # keep 100 outputs

    def _write(self, message):
        msg = (message, datetime.datetime.utcnow(), )
        if self.full():
            self._queue.popleft()
        self._queue.append(msg)

    def write(self, message):
        self._write(message)

    def writelines(self, lines):
        for line in lines:
            self._write(line)

    def flush(self):
        messages = []
        for msg in self._queue:
            message, tm = msg
            messages.insert(0, {
                "message": message,
                "time": str(tm),
            })
        return messages

    def full(self):
        return len(self._queue) >= self._queue.maxlen

    def empty(self):
        return len(self._queue) <= 0


class Service(object):

    def __init__(self, context, *args, **kwargs):
        self._output = OutputBuffer()
        self._event = threading.Event()
        self._t = threading.Thread(target=self._run, args=args, kwargs=kwargs)
        self.on_quit = None
        self._name = None
        self._ctx = context

    def start(self):
        log.debug('Starting service %s ...' % self.__class__)
        self._t.start()
        if self._name is None:
            self._name = self._t.getName()

    def stop(self):
        log.debug('Stopping service %s %d ...' % (self.__class__, self.sid) )
        self._event.set()
        self._t.join()

    def flush_output(self):
        return self._output.flush()

    @property
    def is_alive(self):
        return self._t.is_alive()

    @property
    def sid(self):
        """ Service ID """
        if self._t:
            return self._t.ident
        else:
            return -1

    @property
    def name(self):
        """ Service Name """
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    def _run(self, *args, **kwargs):
        raise NotImplementedError

    __metaclass__ = ABCMeta


class ConsumerService(Service):
    """
    Must specify "user" and "client"(MQ client obj) in "context" arg for ctor
    """

    _autosave = False
    _save_folder = ''

    def __init__(self, context, *args, **kwargs):
        super(ConsumerService, self).__init__(context, *args, **kwargs)
        assert 'user' in self._ctx
        assert 'client' in self._ctx

    def _run(self, *args, **kwargs):
        user = self._ctx['user']
        ucfg = UserConf(user)
        self._save_folder = os.path.abspath(os.path.sep.join([
            ucfg.get(GeneralConfKeys.result_store),
            str(datetime.datetime.utcnow())[0:13]
        ]))
        print(self._save_folder)
        if not os.path.exists(self._save_folder):
            os.makedirs(self._save_folder)

        try:
            self.consume(*args, **kwargs)
        except Exception as err:
            log.exception(err)
        finally:
            if self.on_quit:
                self.on_quit(user, self)

    @property
    def autosave(self):
        return self._autosave

    @autosave.setter
    def autosave(self, value):
        self._autosave = value

    def consume(self, key=None, exchange=None, queue=None):
        """
        Entry method.
        :param key:
        :param exchange:
        :param queue:
        :return:
        """

        output = self._output
        stop_event = self._event

        def on_msg(msg):
            # print(" [x] [%s] %r" % (str(datetime.datetime.now())[:-3], msg))
            if self.autosave:
                self._save_message(msg)
            output.write(json.loads(msg))

        # client = mq.RabbitMQBlockingClient(
        #     host=models.Setting.get('rabbitmq_host'),
        #     port=int(models.Setting.get('rabbitmq_port')),
        #     user=models.Setting.get('rabbitmq_user'),
        #     password=models.Setting.get('rabbitmq_password'),
        #     vhost=models.Setting.get('rabbitmq_vhost')
        # )
        client = self._ctx['client']

        output.write('[*] Waiting for messages. To exit press [x]')

        client.connect()

        if queue:
            output.write('[*] from queue %r' % queue)
            self.name = 'Queue:%s' % queue
            client.consume(queue=queue, callback=on_msg, stop_event=stop_event)
        elif exchange and key:
            output.write('[*] from exchange %r with key %r' % (exchange, key))
            self.name = 'Ex:%s, key:%s' % (exchange, key)
            client.consume_ex(exchange=exchange, key=key, callback=on_msg, stop_event=stop_event)

        output.write('[*] Consumer quit.')
        client.close()

    def _save_message(self, msg):
        obj = json.loads(msg)
        try:
            sender = obj['sender_name']
            receiver = obj['receiver_name']
            uuid = obj['uuid']
            tm = str(datetime.datetime.utcnow()).replace(':', '').replace('.', ' ')[0:-3]
            name = '.'.join([sender, receiver, tm, uuid, 'json'])
            fname = os.path.abspath(os.path.sep.join([self._save_folder, name]))
            with open(fname, mode='wb') as f:
                f.write(msg)
        except Exception as err:
            log.exception(err)


class ServiceUtils(object):
    # ---------------
    # utility related
    # ---------------
    consumers = {}

    @classmethod
    def consumer_on_quit(cls, user, svc):
        if svc:
            if svc.sid in cls.consumers:
                cls.consumers[user].pop(svc.sid)

    @classmethod
    def start_consumer(cls, user, client, queue, key, exchange, autosave=False):
        ctx = {
            'user': user,
            'client': client
        }
        svc = ConsumerService(ctx, queue=queue, key=key, exchange=exchange)
        svc.autosave = autosave
        svc.on_quit = ServiceUtils.consumer_on_quit
        svc.start()
        cls.consumers[user][svc.sid] = svc
        return svc

    @classmethod
    def stop_consumer(cls, user, sid):
        svc = cls.consumers[user].pop(sid)
        svc.stop()