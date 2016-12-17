#!/usr/bin/env python
# coding: utf-8

from django.shortcuts import render, get_list_or_404, get_object_or_404
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseNotFound
from .models import UserConf, ConfKeys, RabbitConfKeys, GeneralConfKeys
from .models import PluginStackModel
from .utils import PropertyDict
from .mq import create_client, MQTypes, get_confs
from .service import ServiceUtils
from .plugin import Plugins
import os
import pathlib

import logging
log = logging.getLogger(__name__)


def t(template):
    return 'pyqueuer/' + template


def test(request):
    return render(request, t('test.html'))


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


@login_required
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
            # for r in request.POST:
            #     print(r + ' - ' + request.POST[r])

            # load message string
            msg_source = request.POST['msg-source'].lower()
            msg_file = request.POST['msg-file']
            msg_data = request.POST['msg-data']
            msg_file_num = request.POST['msg-file-num']
            msg = ''
            if msg_source == 'data':
                msg = msg_data
            elif msg_source == 'file':
                fname = os.path.sep.join([ucfg.get(GeneralConfKeys.data_store), msg_file])
                with open(fname, 'tr') as f:
                    msg = f.read()

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
            message = 'Message sent.'

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
                with q.open('tr') as f:
                    files[q.name] = f.read(150) + '\n ...'
            except Exception as err:
                log.exception(err)

    context = {
        "MQTypes": MQTypes,
        "files": files,
        "message": message,
        "error": error,
    }
    context.update(locals())

    return render(request, t('send.html'), context=context)


@login_required
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
            ServiceUtils.stop_consumer(user=request.user, sid=sid)
        else:
            queue = request.POST['queue']
            exchange = request.POST['exchange']
            key = request.POST['key']
            auto_save = 'check-save' in request.POST and True or False

            conf = get_confs(user=request.user, mq_type=MQTypes.RabbitMQ)
            client = create_client(mq_type=MQTypes.RabbitMQ, conf=conf)

            count = len(ServiceUtils.consumers)
            if count < max_consumers:
                svc = ServiceUtils.start_consumer(user=request.user, client=client, key=key, queue=queue, exchange=exchange, autosave=auto_save)
                if queue:
                    svc.name = 'Queue:%s' % queue
                elif exchange and key:
                    svc.name = 'Exch:%s, Key:%s' % (exchange, key)
            else:
                error = 'You can only start %d consumers' % max

    svcs = ServiceUtils.consumers[request.user] if request.user in ServiceUtils.consumers else {}
    context = {
        "queue": queue,
        "exchange": exchange,
        "key": key,
        "services": svcs,
        "message": msg,
        "error": error,
    }
    return render(request, t('consume.html'), context=context)


@login_required
@require_http_methods(['GET', ])
def output(request):
    if request.user in ServiceUtils.consumers:
        sid = int(request.GET['sid']) if 'sid' in request.GET else None
        if sid in ServiceUtils.consumers[request.user]:
            svc = ServiceUtils.consumers[request.user][sid]
            out = svc.flush_output()
            # print(json.dumps(out))
            # print(len(out))
            return JsonResponse(out, safe=False)
        else:
            return HttpResponseNotFound()


@login_required
@require_http_methods(['GET', 'POST'])
def plugin(request):
    msg = None
    error = None
    stacks = {}

    chk_prefix = 'stack'
    rename_prefix = 'rename'
    spliter = '--'

    mgr = Plugins
    ucfg = UserConf(user=request.user)

    if request.method == 'POST':
        req_rename = {}
        req_stack = []
        for chk in request.POST:
            print(chk, ' - ', request.POST[chk])
            if chk.startswith('%s%s' % (chk_prefix, spliter)):
                req_stack.append(chk)
            elif chk.startswith('%s%s' % (rename_prefix, spliter)):
                tmp = chk.split(spliter)
                old_name = tmp[1]
                new_name = request.POST[chk]
                if old_name != new_name:
                    req_rename[old_name] = new_name

        for chk in req_stack:
            tmp = chk.split(spliter)
            stack = tmp[1]
            plug = tmp[2]
            if stack in req_rename:
                stack = req_rename[stack]
            obj, created = PluginStackModel.objects.get_or_create(
                user=request.user, stack=stack, plugin=plug)
            if created:
                obj.save()
                log.debug('Plugin-stack "%s" added plugin "%s"' % (stack, plug))

        for old_name, new_name in req_rename.items():
            log.info('Plugin-stack "%s" renamed to "%s"' % (old_name, new_name))
            PluginStackModel.objects.filter(user=request.user, stack=old_name).delete()

    plugins = mgr.all()
    for item in PluginStackModel.objects.filter(user=request.user).order_by('stack', 'plugin'):
        if item.stack not in stacks:
            stacks[item.stack] = []
        stacks[item.stack].append(item.plugin)

    context = {
        "plugins": plugins,
        "stacks": stacks,
        "message": msg,
        "error": error,
    }
    return render(request, t('plugin.html'), context=context)
