#!/usr/bin/env python
# coding: utf-8

"""
service module defines general service implementation for MQ
"""

from ..service import ServiceMixin
from .base import IConsume
import simplejson as json
import logging
log = logging.getLogger(__name__)


class MQConsumerService(ServiceMixin):

    def __init__(self, consumer):
        if not isinstance(consumer, IConsume):
            raise ValueError("Consumer must be instance of IConsume")
        self._consumer = consumer
        self._name = 'MQConsumer'

    @property
    def name(self):
        """ Service Name """
        return self._name

    def run(self, output=None, *args, **kwargs):
        """
        see ServiceMixin.run
        :param output:
        :param args:
        :param kwargs:
        :return:
        """
        def on_msg(msg):
            # print(" [x] [%s] %r" % (str(datetime.datetime.now())[:-3], msg))
            try:
                message = json.loads(msg)
            except Exception as err:
                log.exception(err)
                message = msg.decode('utf-8')

            log.debug('Received message: "%s"' % message)
            output.write(message)

        if 'callback' not in kwargs:
            kwargs['callback'] = on_msg

        # Assign name. TODO: change the name.
        sb = [str(type(self._consumer)).split('.')[-1][:-2]]
        for k, v in kwargs.items():
            sb.append(', %s=%s' % (k, v))
        self._name = ''.join(sb)

        # consuming
        output.write('[*] Waiting for messages.')

        consumer = self._consumer
        consumer.connection.connect()

        consumer.consume(*args, **kwargs)
        output.write('[*] Consumer quit.')

        consumer.connection.disconnect()
        log.debug('Consumer quit')
