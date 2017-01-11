#!/usr/bin/env python
# coding: utf-8

"""
service modules defines classes to construct a general service.
TODO: need to be improved.
"""

import abc
import threading
from .utils import OutputBuffer
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
        self.on_quit = lambda wrapper: log.debug('%s is quiting' % wrapper)

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
            cls._private[user] = ServiceManager()
        return cls._private[user]
