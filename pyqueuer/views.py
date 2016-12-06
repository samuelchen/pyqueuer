#!/usr/bin/env python
# coding: utf-8

from django.shortcuts import render, get_list_or_404, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseNotFound
from .models import UserConf, ConfKeys, RabbitConfKeys, GeneralConfKeys
from .utils import PropertyDict
from .mq import create_client, MQTypes, get_confs
from .service import ServiceUtils
import os
import pathlib

import logging
log = logging.getLogger(__name__)


def t(template):
    return 'pyqueuer/' + template


@require_http_methods(['GET', ])
def index(request):
    if request.user.is_authenticated:
        pass
    elif request.user.is_staff:
        pass
    else:
        pass
    context = {
        # "setting_keys": models.SETTING_NAMES,
    }
    return render(request, t('index.html'), context=context)


@login_required
@require_http_methods(['GET', 'POST'])
def setting(request):
    message = None
    error = None
    # output = StringIO()
    ucfg = UserConf(request.user)

    if request.method == 'POST':
        if 'config_file' in request.POST:
            config_file = request.POST['config_file']
            # Utils.import_config(config_file, output=output)
            # message = output.getvalue()
        else:
            for options in ConfKeys.values():
                for value in options.values():
                    print(value, request.POST[value])
                    ucfg.set(value, request.POST[value])
            message = 'Setting saved.'

    confs = PropertyDict()

    count = len(ucfg.all())
    for section, options in ConfKeys.items():
        confs[section] = PropertyDict().fromkeys(options.values())
        count -= len(options)
    if count < 0:
        ucfg.initialize()

    for opt in ucfg.all():
        for section in ConfKeys.keys():
            if opt.name in confs[section].keys():
                confs[section][opt.name] = opt.value
                break

    context = {
        "confs": confs,
        "message": message,
        "error": error,
    }
    return render(request, t('setting.html'), context=context)


@require_http_methods(['GET', 'POST'])
def send(request):
    message = None
    error = None

    ucfg = UserConf(user=request.user)
    queue = ucfg.get(RabbitConfKeys.queue_out)
    exchange = ucfg.get(RabbitConfKeys.topic_out)
    key = ucfg.get(RabbitConfKeys.key_out)
    # outupt = StringIO()

    try:
        if request.method == 'POST':
            for r in request.POST:
                print(r + ' - ' + request.POST[r])

            # load message string
            msg_source = request.POST['msg-source']
            msg_file = request.POST['msg-file']
            msg_data = request.POST['msg-data']
            msg = ''
            if msg_source == 'data':
                msg = msg_data
            elif msg_source == 'file':
                fname = os.path.sep.join([ucfg.get(GeneralConfKeys.data_store), msg_file])
                with open(fname) as f:
                    msg = f.read(140) + '\n ...'

            # overriding plugins
            is_plugin_enabled = False
            count = 'check-count' in request.POST and int(request.POST['count']) or 1
            auto_uuid = 'check-uuid' in request.POST and True or False
            auto_time = 'check-time' in request.POST and True or False
            timeout = 'check-timeout' in request.POST and int(request.POST['timeout']) or -1

            # selected MQ
            mq = request.POST['mq']
            if mq == MQTypes.RabbitMQ:
                queue = request.POST['queue']
                exchange = request.POST['exchange']
                key = request.POST['key']
            elif mq == MQTypes.Kafka:
                pass
            else:
                raise Exception('Selected MQ "%s" is not supported' % mq)

            conf = get_confs(user=request.user, mq_type=mq)
            client = create_client(mq_type=mq, conf=conf)
            if is_plugin_enabled:
                # process plugins to override msg
                # process_plugin('plugin', msg)
                pass
            client.send(msg, queue)

    except KeyError as err:
        log.exception(err)
        error = 'You must specify %s' % str(err)
    except Exception as err:
        log.exception(err)
        error = str(err)

    files = {}
    p = pathlib.Path(ucfg.get(GeneralConfKeys.data_store))
    if p.is_dir():
        for q in p.iterdir():
            try:
                with q.open() as f:
                    files[q.name] = f.read()
            except:
                pass

    context = {
        "MQTypes": MQTypes,
        "files": files,
        "message": message,
        "error": error,
    }
    context.update(locals())

    return render(request, t('send.html'), context=context)

@require_http_methods(['GET', 'POST'])
def consume(request):
    msg = None
    error = None


    ucfg = UserConf(user=request.user)
    queue = ucfg.get(RabbitConfKeys.queue_in)
    exchange = ucfg.get(RabbitConfKeys.topic_in)
    key = ucfg.get(RabbitConfKeys.key_in)
    max_consumers = 5

    if request.method == 'POST':

        if 'sid' in request.POST:
            sid = int(request.POST['sid'])
            ServiceUtils.stop_consumer(sid=sid)
        else:
            queue = request.POST['queue']
            exchange = request.POST['exchange']
            key = request.POST['key']
            auto_save = 'check-save' in request.POST and True or False

            count = len(ServiceUtils.consumers)
            if count < max_consumers:
                svc = ServiceUtils.start_consumer(key=key, queue=queue, exchange=exchange, autosave=auto_save)
                if queue:
                    svc.name = 'Queue:%s' % queue
                elif exchange and key:
                    svc.name = 'Exch:%s, Key:%s' % (exchange, key)
            else:
                error = 'You can only start %d consumers' % max

    svcs = ServiceUtils.consumers
    context = {
        "queue": queue,
        "exchange": exchange,
        "key": key,
        "services": svcs,
        "message": msg,
        "error": error,
    }
    return render(request, t('consume.html'), context=context)