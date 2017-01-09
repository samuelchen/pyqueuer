#!/usr/bin/env python
# coding: utf-8

"""
views module defines function views for all pages.
"""

from django.conf import settings
from django.shortcuts import render, get_list_or_404, get_object_or_404
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseBadRequest
from .models import UserConf, ConfKeys, RabbitConfKeys, GeneralConfKeys, KafkaConfKeys
from .models import PluginStackModel
from .utils import PropertyDict
from .mq import MQClientFactory, MQTypes
from .service import ServiceManager, MQConsumerService
from .plugin import Plugins
import os
import pathlib
from collections import OrderedDict

import logging

log = logging.getLogger(__name__)

# used to split a id/name of a html tag.
html_tag_splitter = '♥'
# used to stack all plugins
reversed_stack_name = '_'


# to render full template path
def t(template):
    return 'pyqueuer/' + template


# test view for some test purpose
if __debug__ and settings.DEBUG:
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
                    # print(value, request.POST[value])
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

    plugins = Plugins.all_metas()

    ucfg = UserConf(user=request.user)

    rabbit_1 = ucfg.get(RabbitConfKeys.queue_out)
    rabbit_2 = ucfg.get(RabbitConfKeys.topic_out)
    rabbit_3 = ucfg.get(RabbitConfKeys.key_out)

    kafka_1 = ucfg.get(KafkaConfKeys.topic_out)
    kafka_2 = ''

    try:
        if request.method == 'POST':
            # for r in request.POST:
            #     print(r + ' - ' + request.POST[r])

            # load message string
            msg_source = request.POST['msg-source']
            msg_source_idx = request.POST['msg-source-idx']
            msg_file = request.POST['msg-file']
            msg_data = request.POST['msg-data']
            msg_file_idx = request.POST['msg-file-idx']
            msg = ''
            if msg_source == 'Data':
                msg = msg_data
            elif msg_source == 'File':
                fname = os.path.sep.join([ucfg.get(GeneralConfKeys.data_store), msg_file])
                with open(fname, 'tr') as f:
                    msg = f.read()

            # overriding plugins
            stack = request.POST['stack']
            stack_idx = request.POST['stack-idx']
            for req in request.POST:
                if req.startswith('plugin' + html_tag_splitter):
                    tmp = req.split(html_tag_splitter)
                    plugins[tmp[1]].checked = True

            # selected MQ
            mq = request.POST['mq']
            mq_idx = request.POST['mq-idx']
            params = {}
            if mq == MQTypes.RabbitMQ:
                params = {
                    "queue": request.POST['rabbit_1'],     # queue
                    "topic": request.POST['rabbit_2'],     # topic
                    "key": request.POST['rabbit_3'],     # key
                }
            elif mq == MQTypes.Kafka:
                params = {
                    "topic": request.POST['kafka_1'],     # topic
                    "key": request.POST['kafka_2'],     # key
                }
            else:
                raise Exception('Selected MQ "%s" is not supported' % mq)

            # process plugins to override msg
            for plugin in plugins.values():
                if plugin.checked:
                    if plugin.plugin_object.is_auto_value:
                        msg = plugin.plugin_object.update(msg)
                    else:
                        val = request.POST['pluginv%s%s' % (html_tag_splitter, plugin.name)]
                        if not val:
                            raise ValueError('You must specify value for plugin "%s"' % plugin.name)
                        plugin.value = val
                        msg = plugin.plugin_object.update(msg, val)

            # produce message
            conf = MQClientFactory.get_confs(mq_type=mq, user=request.user)
            client = MQClientFactory.create_producer(mq_type=mq, conf=conf)
            client.produce(msg, **params)
            message = 'Message sent.'

    except KeyError as err:
        log.exception(err)
        error = 'You must specify %s' % str(err)
    except Exception as err:
        log.exception(err)
        error = str(err)

    files = OrderedDict()
    p = ucfg.get(GeneralConfKeys.data_store)
    if p:
        p = pathlib.Path(p)
        if p.is_dir():
            for q in sorted(p.iterdir()):
                try:
                    with q.open('tr') as f:
                        files[q.name] = f.read(150) + '\n ...'
                except Exception as err:
                    log.exception(err)
    else:
        files['no data_store'] = 'Please specify your data_store in setting.'

    # prepare user plugin stacks
    stacks = OrderedDict()
    stacks[reversed_stack_name] = []        # stack for all plugin
    for plugin in plugins.values():
        stacks[reversed_stack_name].append(plugin.name)
    for item in PluginStackModel.objects.filter(user=request.user).order_by('stack', 'plugin'):
        if item.stack not in stacks:
            stacks[item.stack] = []
        stacks[item.stack].append(item.plugin)



    context = {
        "MQTypes": MQTypes,
        "files": files,
        "plugins": plugins,
        "stacks": stacks,
        "splitter": html_tag_splitter,
        "reversed_stack_name": reversed_stack_name,
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
    max_consumers = 5

    ucfg = UserConf(user=request.user)

    rabbit_1 = ucfg.get(RabbitConfKeys.queue_in)
    rabbit_2 = ucfg.get(RabbitConfKeys.topic_in)
    rabbit_3 = ucfg.get(RabbitConfKeys.key_in)

    kafka_1 = ucfg.get(KafkaConfKeys.topic_in)
    kafka_2 = ''

    if request.method == 'POST':

        if 'sid' in request.POST:
            # close consumer
            sid = int(request.POST['sid'])
            ServiceManager.private(user=request.user).stop(sid=sid)
        else:

            # selected MQ
            mq, mq_idx, params = _handle_mq_tabs_request(request)

            # other configs
            auto_save = 'check-save' in request.POST and True or False

            # client
            conf = MQClientFactory.get_confs(mq_type=MQTypes.RabbitMQ, user=request.user)
            client = MQClientFactory.create_consumr(mq_type=MQTypes.RabbitMQ, conf=conf)

            svc_mgr = ServiceManager.private(user=request.user)
            count = len(svc_mgr.all())
            if count < max_consumers:
                conf = MQClientFactory.get_confs(mq_type=mq, user=request.user)
                consumer = MQClientFactory.create_consumr(mq_type=mq, conf=conf)
                service = MQConsumerService(consumer=consumer)
                svc = svc_mgr.start(service, autosave=auto_save, **params)

            else:
                error = 'You can only start %d consumers' % max_consumers

    svcs = ServiceManager.private(user=request.user).all()
    context = {
        "MQTypes": MQTypes,
        "services": svcs,
        "message": msg,
        "error": error,
    }
    context.update(locals())
    return render(request, t('consume.html'), context=context)


@login_required
@require_http_methods(['GET', ])
def output(request):
    svcs = ServiceManager.private(user=request.user).all()
    # print('services:', svcs)
    if svcs:
        sid = int(request.GET['sid']) if 'sid' in request.GET else None
        if sid in svcs:
            svc = svcs[sid]
            out = svc.flush_output()
            # print(json.dumps(out))
            # print(len(out))
            return JsonResponse(out, safe=False)
    return HttpResponseNotFound()


@login_required
@require_http_methods(['GET', 'POST'])
def plugin(request):
    msg = None
    error = None
    stacks = OrderedDict()

    chk_prefix = 'stack'
    rename_prefix = 'rename'

    ucfg = UserConf(user=request.user)

    if request.method == 'POST':
        req_rename = {}
        req_stack = []
        req_del = []

        # deleted stacks
        if 'del-stacks' in request.POST:
            req_del = request.POST['del-stacks'].split(',')
            for req in req_del:
                if req:
                    log.info('Plugin-stack "%s" is deleted.' % req)
                    PluginStackModel.objects.filter(user=request.user, stack=req).delete()

        for req in request.POST:
            # print(req, ' - ', request.POST[req])

            # all stacks with their enabled plugins
            if req.startswith('%s%s' % (chk_prefix, html_tag_splitter)):
                req_stack.append(req)
            # all renamed stacks
            elif req.startswith('%s%s' % (rename_prefix, html_tag_splitter)):
                tmp = req.split(html_tag_splitter)
                old_name = tmp[1]
                new_name = request.POST[req]
                if old_name != new_name and new_name != reversed_stack_name:
                    req_rename[old_name] = new_name

        # update stacks with plugins (renamed as new)
        for req in req_stack:
            tmp = req.split(html_tag_splitter)
            stack = tmp[1]
            plug = tmp[2]

            # this stack need to be renamed
            if stack in req_rename:
                stack = req_rename[stack]
            obj, created = PluginStackModel.objects.get_or_create(
                user=request.user, stack=stack, plugin=plug)
            if created:
                obj.save()
                log.debug('Plugin-stack "%s" added plugin "%s"' % (stack, plug))

        # rename stacks (just remove old-names, new-names are updated above)
        for old_name, new_name in req_rename.items():
            log.info('Plugin-stack "%s" renamed to "%s"' % (old_name, new_name))
            PluginStackModel.objects.filter(user=request.user, stack=old_name).delete()

    plugins = Plugins.all()
    for item in PluginStackModel.objects.filter(user=request.user).order_by('stack', 'plugin'):
        if item.stack not in stacks:
            stacks[item.stack] = []
        stacks[item.stack].append(item.plugin)

    context = {
        "splitter": html_tag_splitter,
        "reversed_stack_name": reversed_stack_name,
        "plugins": plugins,
        "stacks": stacks,
        "message": msg,
        "error": error,
    }
    return render(request, t('plugin.html'), context=context)


# --- convenience functions ---

def _handle_mq_tabs_request(request):
    """
    Handle the POST request for MQ selection tabs.
    The HTML codes should be generated from "pyqueuer/includes/mq-sel-tab.html". (Django include)
    Will handle selected MQ name, selected MQ tab index and all posted fields depends on selected MQ.
    :param request: Django request object.
    :return: tuple of ("Selected MQ Name", "Tab Index of selected MQ", "Fields Dict of selected MQ")
    """
    mq = request.POST['mq']
    mq_idx = request.POST['mq-idx']
    params = {}
    if mq == MQTypes.RabbitMQ:
        params = {
            "queue": request.POST['rabbit_1'],     # queue
            "topic": request.POST['rabbit_2'],     # topic
            "key": request.POST['rabbit_3'],     # key
        }
    elif mq == MQTypes.Kafka:
        params = {
            "topic": request.POST['kafka_1'],     # topic
            "key": request.POST['kafka_2'],     # key
        }
    else:
        raise Exception('Selected MQ "%s" is not supported' % mq)

    return mq, mq_idx, params