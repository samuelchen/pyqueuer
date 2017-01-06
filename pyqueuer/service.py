#!/usr/bin/env python
# coding: utf-8

"""
service modules defines classes to construct a general service.
TODO: need to be improved.
"""

import abc
import threading
import datetime
import simplejson as json
import os
from .models import UserConf, GeneralConfKeys
from .utils import OutputBuffer
from .mq.base import IConsume
# from .mq import RabbitMQConsumer, KafkaConsumer

import logging

log = logging.getLogger(__name__)


class ServiceMixin(object):
    """
    Service mixin interface.
    Inherit this class to implement service.
    The service instance will be handle by Service class
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def name(self):
        pass

    @abc.abstractmethod
    def run(self, output, *args, **kwargs):
        """
        Service entry point. ServiceWrapper will call this method to run service.
        :param output: The file-like output buffer which ServiceWrapper will passed in.
                        Service implementation can use it to write output.
        :param args: Arguments passed to run service
        :param kwargs: Named key-value arguments passed to run service.
        :return:
        """
        pass


class ServiceWrapper(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, service, *args, **kwargs):
        """
        Wrap a service for running in thread.
        :param service: An instance of ServiceMixin which holds the object and functions.
        :param args: Arguments passed to run service
        :param kwargs: Named key-value arguments passed to run service.
        :return:
        """
        if not isinstance(service, ServiceMixin):
            raise ValueError("Service object must be an instance of ServiceMixin")
        self._service = service
        # self._owner = owner
        self._output = OutputBuffer()
        self._event = threading.Event()
        if 'stop_event' not in kwargs:
            kwargs['stop_event'] = self._event
        self._t = threading.Thread(target=self.__run_service, args=args, kwargs=kwargs)
        self.on_quit = None

    def start(self):
        log.debug('Starting service %s ...' % self.__class__)
        self._t.start()

    def stop(self):
        log.debug('Stopping service %s %d ...' % (self.__class__, self.sid))
        self._event.set()
        self._t.join()

    def flush_output(self):
        return self._output.flush()

    @property
    def service(self):
        """ The ServiceMixin instance """
        return self._service

    # @property
    # def owner(self):
    #     """ Service owner """
    #     return self._owner

    @property
    def is_alive(self):
        """ Check if service is still running """
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
        return self._service.name

    def __run_service(self, *args, **kwargs):
        """
        Run a service.
        :param args:
        :param kwargs:
        :return:
        """
        try:
            self._service.run(output=self._output, *args, **kwargs)
        except Exception as err:
            log.exception(err)
        finally:
            if self.on_quit:
                self.on_quit(wrapper=self)


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

        sb = []
        sb.append(str(type(self._consumer)).split('.')[-1][:-2])
        for k, v in kwargs.items():
            sb.append(', %s=%s' % (k, v))
        self._name = ''.join(sb)

        # if 'queue' in kwargs:
        #     self._name = 'Queue:%s' % kwargs['queue']
        # elif 'topic' in kwargs and 'key' in kwargs:
        #     self._name = 'Topic:%s, Key:%s' % (kwargs['topic'], kwargs['key'])

        output.write('[*] Waiting for messages.')

        consumer = self._consumer
        consumer.connection.connect()

        consumer.consume(*args, **kwargs)
        output.write('[*] Consumer quit.')

        consumer.connection.disconnect()
        log.debug('Consumer quit')


class ServiceManager(object):

    _public = None
    _private = {}

    def __init__(self):
        self._services = {}

    def start(self, service, *args, **kwargs):
        """
        Start a service in.
        :param service: An instance of ServiceMixin which holds the object and functions.
        :param args: Arguments passed to run service
        :param kwargs: Named key-value arguments passed to run service.
        :return: The wrapper object of the service.
        """
        if not isinstance(service, ServiceMixin):
            raise ValueError("Service object must be an instance of ServiceMixin")

        wrapper = ServiceWrapper(service, *args, **kwargs)
        wrapper.on_quit = self.__on_quit
        wrapper.start()
        assert wrapper.sid not in self._services
        self._services[wrapper.sid] = wrapper
        log.debug('Service %s:"%s" started.' % (wrapper.sid, wrapper.name))
        return wrapper

    def stop(self, sid):
        """
        Stop a running service by given service id.
        :param sid: Service ID.
        :return:
        """
        if sid in self._services:
            wrapper = self._services.pop(sid)
            wrapper.stop()

    def __on_quit(self, wrapper):
        """
        PostEvent will be triggered when a service quit
        :param wrapper: An instance of ServiceMixin which holds the object and functions.
        :return:
        """
        assert isinstance(wrapper, ServiceWrapper)
        if wrapper:
            if wrapper.sid in self._services:
                self._services.pop(wrapper.sid)

    def all(self):
        """ all service """
        return self._services

    @classmethod
    def public(cls):
        if cls._public is None:
            cls._public = ServiceManager()
        return cls._public

    @classmethod
    def private(cls, user):
        if user not in cls._private:
            # print('private not found')
            cls._private[user] = ServiceManager()
        else:
            # print('private found:', cls._private[user], '  all:', cls._private[user].all())
            pass
        return cls._private[user]

# class ServiceUtils(object):
#     # ---------------
#     # utility related
#     # ---------------
#     services = {}
#
#     @classmethod
#     def service_on_quit(cls, wrapper):
#         """
#         PostEvent will be triggered when a service quit.
#         :param wrapper: An instance of ServiceMixin which holds the object and functions.
#         :return:
#         """
#         assert isinstance(wrapper, ServiceWrapper)
#         if wrapper:
#             owner = wrapper.owner
#             if owner in cls.services:
#                 if wrapper.sid in cls.services[owner]:
#                     cls.services[owner].pop(wrapper.sid)
#
#     @classmethod
#     def start_service(cls, service, owner=None, *args, **kwargs):
#         """
#         Start a service in.
#         :param service: An instance of ServiceMixin which holds the object and functions.
#         :param owner: The service owner. If specified, service will store in owner's space. If None, use global space.
#         :param args: Arguments passed to run service
#         :param kwargs: Named key-value arguments passed to run service.
#         :return: The wrapper object of the service.
#         """
#         if not isinstance(service, ServiceMixin):
#             raise ValueError("Service object must be an instance of ServiceMixin")
#
#         wrapper = ServiceWrapper(service, owner, *args, **kwargs)
#         wrapper.on_quit = ServiceUtils.service_on_quit
#         wrapper.start()
#
#         if owner not in cls.services:
#             cls.services[owner] = {}
#         cls.services[owner][wrapper.sid] = wrapper
#         return wrapper
#
#     @classmethod
#     def stop_service(cls, sid, owner=None):
#         """
#         Stop a running service.
#         :param sid: Service ID.
#         :param owner: The service owner. If specified, service will store in owner's space. If None, use global space.
#         :return:
#         """
#         if owner in cls.services:
#             wrapper = cls.services[owner].pop(sid)
#             wrapper.stop()


# class Service(object):
#     __metaclass__ = abc.ABCMeta
#
#     def __init__(self, service, *args, **kwargs):
#         """
#
#         :param service: ServiceMixin instance to run.
#         :param args:
#         :param kwargs:
#         :return:
#         """
#         if not isinstance(service, ServiceMixin):
#             raise ValueError("Service object must be an instance of ServiceMixin")
#
#         self._output = OutputBuffer()
#         self._event = threading.Event()
#         self._t = threading.Thread(target=self._run, args=args, kwargs=kwargs)
#         self.on_quit = None
#         self._name = None
#         self._ctx = context
#
#     def start(self):
#         log.debug('Starting service %s ...' % self.__class__)
#         self._t.start()
#         if self._name is None:
#             self._name = self._t.getName()
#
#     def stop(self):
#         log.debug('Stopping service %s %d ...' % (self.__class__, self.sid))
#         self._event.set()
#         self._t.join()
#
#     def flush_output(self):
#         return self._output.flush()
#
#     @property
#     def is_alive(self):
#         return self._t.is_alive()
#
#     @property
#     def sid(self):
#         """ Service ID """
#         if self._t:
#             return self._t.ident
#         else:
#             return -1
#
#     @property
#     def name(self):
#         """ Service Name """
#         return self._name
#
#     @name.setter
#     def name(self, value):
#         self._name = value
#
#     def _run(self, *args, **kwargs):
#         raise NotImplementedError
#
#
#
# class ConsumerService(Service):
#     """
#     Must specify "user" and "client"(MQ client obj) in "context" arg for ctor
#     """
#
#     _autosave = False
#     _save_folder = ''
#
#     def __init__(self, context, *args, **kwargs):
#         super(ConsumerService, self).__init__(context, *args, **kwargs)
#         assert 'user' in self._ctx
#         assert 'client' in self._ctx
#         client = self._ctx['client']
#         assert
#
#     def _run(self, *args, **kwargs):
#         user = self._ctx['user']
#         ucfg = UserConf(user)
#         self._save_folder = os.path.abspath(os.path.sep.join([
#             ucfg.get(GeneralConfKeys.result_store),
#             str(datetime.datetime.utcnow())[0:13]
#         ]))
#         if not os.path.exists(self._save_folder):
#             os.makedirs(self._save_folder)
#
#         try:
#             self.consume(*args, **kwargs)
#         except Exception as err:
#             log.exception(err)
#         finally:
#             if self.on_quit:
#                 self.on_quit(user, self)
#
#     @property
#     def autosave(self):
#         return self._autosave
#
#     @autosave.setter
#     def autosave(self, value):
#         self._autosave = value
#
#     def consume(self, key=None, exchange=None, queue=None):
#         """
#         Entry method.
#         :param key:
#         :param exchange:
#         :param queue:
#         :return:
#         """
#
#         output = self._output
#         stop_event = self._event
#
#         def on_msg(msg):
#             # print(" [x] [%s] %r" % (str(datetime.datetime.now())[:-3], msg))
#             try:
#                 message = json.loads(msg)
#             except:
#                 message = msg.decode('utf-8')
#             log.debug('Received message: "%s"' % message)
#             if self.autosave:
#                 self._save_message(msg)
#             output.write(message)
#
#         client = self._ctx['client']
#
#         output.write('[*] Waiting for messages.')
#
#         client.connection.connect()
#
#         if queue:
#             output.write('[*] from queue %r' % queue)
#             self.name = 'Queue:%s' % queue
#             client.consume(queue=queue, callback=on_msg, stop_event=stop_event)
#         elif exchange and key:
#             output.write('[*] from exchange %r with key %r' % (exchange, key))
#             self.name = 'Ex:%s, key:%s' % (exchange, key)
#             client.consume(topic=exchange, key=key, callback=on_msg, stop_event=stop_event)
#
#         output.write('[*] Consumer quit.')
#         client.connection.disconnect()
#
#     def _save_message(self, msg):
#         # obj = json.loads(msg)
#         try:
#             # TODO: plugin to obtain more messages to generate better name
#             # sender = obj['sender_name']
#             # receiver = obj['receiver_name']
#             # uuid = obj['uuid']
#             tm = str(datetime.datetime.utcnow()).replace(':', '').replace('.', '_').replace(' ', '_')[0:-3]
#             # name = '.'.join([sender, receiver, tm, uuid, 'json'])
#             name = '.'.join([tm, 'json'])
#             fname = os.path.abspath(os.path.sep.join([self._save_folder, name]))
#             with open(fname, mode='wb') as f:
#                 f.write(msg)
#         except Exception as err:
#             log.exception(err)
#
#
# class ServiceUtils(object):
#     # ---------------
#     # utility related
#     # ---------------
#     consumers = {}
#
#     @classmethod
#     def consumer_on_quit(cls, user, svc):
#         if svc:
#             if user in cls.consumers:
#                 if svc.sid in cls.consumers[user]:
#                     cls.consumers[user].pop(svc.sid)
#
#     @classmethod
#     def start_consumer(cls, user, client, queue, key, topic, autosave=False):
#         ctx = {
#             'user': user,
#             'client': client
#         }
#         svc = ConsumerService(ctx, queue=queue, key=key, exchange=topic)
#         svc.autosave = autosave
#         svc.on_quit = ServiceUtils.consumer_on_quit
#         svc.start()
#         if user not in cls.consumers:
#             cls.consumers[user] = {}
#         cls.consumers[user][svc.sid] = svc
#         return svc
#
#     @classmethod
#     def stop_consumer(cls, user, sid):
#         if user in cls.consumers:
#             svc = cls.consumers[user].pop(sid)
#             svc.stop()