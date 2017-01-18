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
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseBadRequest
from .models import UserConf, ConfKeys, RabbitConfKeys, GeneralConfKeys, KafkaConfKeys
from .models import PluginStackModel
from .utils import PropertyDict
from .mq import MQClientFactory, MQTypes
from .mq.service import MQConsumerService
from .service import ServiceManager
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

    # count = len(ucfg.all())
    for section, options in ConfKeys.items():
        confs[section] = PropertyDict().fromkeys(options.values())
        # count -= len(options)
    # if count < 0:
    #     ucfg.initialize()

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
    errors = []

    plugins_updater = Plugins.individual_updaters()
    plugins_batch = Plugins.batch_updaters()
    plugins_all = Plugins.all()
    plugins_checked = set()
    plugin_args = {}

    ucfg = UserConf(user=request.user)

    mq_form_fields, mq_params = _handle_mq_selection_tabs(request)

    # prepare user plugin stacks
    stacks = OrderedDict()
    stacks[reversed_stack_name] = []        # stack for all plugin
    for c_plugins in plugins_all.values():
        for plug in c_plugins.values():
            stacks[reversed_stack_name].append(plug.name)
    for item in PluginStackModel.objects.filter(user=request.user).order_by('stack', 'plugin'):
        if item.stack not in stacks:
            stacks[item.stack] = []
        stacks[item.stack].append(item.plugin)

    try:
        if request.method == 'POST':
            # for r in request.POST:
            #     if r.startswith('plugin' + html_tag_splitter):
            #         print(r + ' - ' + request.POST[r])

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
                file = os.path.sep.join([ucfg.get(GeneralConfKeys.data_store), msg_file])
                with open(file, 'tr') as f:
                    msg = f.read()

            # plugins stacks
            stack = request.POST['stack']
            stack_idx = request.POST['stack-idx']
            plugin_prefix = 'plugin' + html_tag_splitter
            for req in request.POST:
                if req.startswith(plugin_prefix):
                    tmp = req.split(html_tag_splitter)
                    name = tmp[1]
                    plugins_checked.add(name)

            # produce message
            conf = MQClientFactory.get_confs(mq_type=mq_form_fields['mq'], user=request.user)
            client = MQClientFactory.create_producer(mq_type=mq_form_fields['mq'], conf=conf)

            def send_a_message(the_msg):
                # handle individual updater plugins to override msg
                for p in plugins_updater.values():
                    if p.name in plugins_checked and p.name in stacks[stack]:
                        args = {}
                        try:
                            for parm in p.plugin_object.params:
                                t = html_tag_splitter.join(['pluginv', p.name, parm])
                                # if t not in request.POST:
                                #     errors.append('You must specify "%s" for plugin "%s"' % (parm, p.name))
                                #     continue
                                args[parm] = request.POST[t]

                            the_msg = p.plugin_object.update(the_msg, args)
                        except Exception as err:
                            e = 'Plugin "%s" fail. %s: %s.' % (p.name, type(err).__name__, str(err))
                            errors.append(e)
                            log.warn(e + 'Message is: %s' % the_msg)
                        plugin_args[p.name] = args
                client.produce(the_msg, **mq_params)

            sent = False
            # handle batch updater plugins to override sending process
            for plug in plugins_batch.values():
                if plug.name in plugins_checked and plug.name in stacks[stack]:
                    log.debug('Process BatchUpdater plugin "%s". params=%s' % (plug.name, plug.plugin_object.params))
                    plug.plugin_object.send_func = send_a_message
                    plug.plugin_object.origin_message = msg     # set origin message
                    plug.plugin_object.update_message(None)     # clear current message
                    arguments = {}
                    try:
                        for parameter in plug.plugin_object.params:
                            tag_name = html_tag_splitter.join(['pluginv', plug.name, parameter])
                            # if t not in request.POST:
                            #     errors.append('You must specify "%s" for plugin "%s"' % (parameter, plug.name))
                            #     continue
                            arguments[parameter] = request.POST[tag_name]
                        plug.plugin_object.run(arguments)
                        sent = True
                    except Exception as err:
                        e = 'Plugin "%s" fail. %s: %s.' % (plug.name, type(err).__name__, str(err))
                        errors.append(e)
                        log.warn(e + 'Message is: %s' % msg)
                    plugin_args[plug.name] = arguments
            if not sent:
                send_a_message(msg)

            message = 'Message sent.'

    except KeyError as err:
        errors.append('You must specify %s' % str(err))

    files = OrderedDict()
    data_store_path = ucfg.get(GeneralConfKeys.data_store)
    if data_store_path:
        data_store_path = pathlib.Path(data_store_path)
        if data_store_path.is_dir():
            for file in sorted(data_store_path.iterdir()):
                try:
                    with file.open('tr') as f:
                        files[file.name] = f.read()    # f.read(150) + '\n ...'
                except Exception as err:
                    e = 'Fail to read file %s. Error: %s' % (file.name, str(err))
                    errors.append(e)
                    log.debug(e)
    else:
        files['no data_store'] = 'Please specify your data_store in setting.'

    context = {
        "MQTypes": MQTypes,
        "files": files,
        "plugins": plugins_all,
        "checked": plugins_checked,
        "stacks": stacks,
        "splitter": html_tag_splitter,
        "reversed_stack_name": reversed_stack_name,
        "message": message,
        "error": '<br/>'.join(errors),
    }
    context.update(mq_form_fields)
    context.update(locals())

    return render(request, t('send.html'), context=context)


@login_required
@require_http_methods(['GET', 'POST'])
def consume(request):
    msg = None
    error = None
    max_consumers = 5

    # handle MQ selection form
    mq_form_fields, params = _handle_mq_selection_tabs(request)

    if request.method == 'POST':

        if 'sid' in request.POST:
            # close consumer
            sid = int(request.POST['sid'])
            ServiceManager.private(user=request.user).stop(sid=sid)
        else:

            # other configs
            auto_save = 'check-save' in request.POST and True or False

            # start service
            svc_mgr = ServiceManager.private(user=request.user)
            count = len(svc_mgr.all())
            if count < max_consumers:
                conf = MQClientFactory.get_confs(mq_type=mq_form_fields['mq'], user=request.user)
                consumer = MQClientFactory.create_consumer(mq_type=mq_form_fields['mq'], conf=conf)
                service = MQConsumerService(consumer=consumer)
                svc_mgr.start(service, autosave=auto_save, **params)

            else:
                error = 'You can only start %d consumers' % max_consumers

    svcs = ServiceManager.private(user=request.user).all()
    context = {
        "MQTypes": MQTypes,
        "services": svcs,
        "message": msg,
        "error": error,
    }
    context.update(mq_form_fields)
    return render(request, t('consume.html'), context=context)


@login_required
@require_http_methods(['GET', ])
def output(request):
    svcs = ServiceManager.private(user=request.user).all()
    sid = int(request.GET['sid']) if 'sid' in request.GET else None
    if sid in svcs:
        svc = svcs[sid]
        out = svc.flush_output()
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

    for item in PluginStackModel.objects.filter(user=request.user).order_by('stack', 'plugin'):
        if item.stack not in stacks:
            stacks[item.stack] = []
        stacks[item.stack].append(item.plugin)

    plugins = Plugins.all(refresh=True)

    context = {
        "splitter": html_tag_splitter,
        "reversed_stack_name": reversed_stack_name,
        "plugins": plugins,
        "stacks": stacks,
        "message": msg,
        "error": error,
    }
    return render(request, t('plugin.html'), context=context)


@sensitive_post_parameters()
@csrf_protect
def register(request):
    msg = None
    error = []

    if request.method == "POST":
        form = UserCreationForm(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')
        else:
            error = form.errors
    else:
        form = UserCreationForm()

    context = {
        'form': form,
        'message': msg,
        'error': error,
    }

    return render(request, 'registration/register.html', context)


# --- convenience functions ---

def _handle_mq_selection_tabs(request):
    """
    Handle the POST request for MQ selection tabs.
    The HTML codes should be generated from "pyqueuer/includes/mq-sel-tab.html". (Django include)
    Will handle selected MQ name, selected MQ tab index and all posted fields depends on selected MQ.
    :param request: Django request object.
    :return: tuple of ("MQ selection form fields dict", "Parameters dict for MQ clients/services")
    """
    ucfg = UserConf(user=request.user)

    params = {}
    form_fields = {
        "mq": request.POST['mq'] if 'mq' in request.POST else MQTypes.RabbitMQ,
        "mq_idx": request.POST['mq-idx'] if 'mq-idx' in request.POST else 0,
        "rabbit_queue": request.POST['rabbit_queue'] if 'rabbit_queue' in request.POST else ucfg.get(RabbitConfKeys.queue_in),
        "rabbit_topic": request.POST['rabbit_topic'] if 'rabbit_topic' in request.POST else ucfg.get(RabbitConfKeys.topic_in),
        "rabbit_key": request.POST['rabbit_key'] if 'rabbit_key' in request.POST else ucfg.get(RabbitConfKeys.key_in),
        "kafka_topic": request.POST['kafka_topic'] if 'kafka_topic' in request.POST else ucfg.get(KafkaConfKeys.topic_in),
        "kafka_key": request.POST['kafka_key'] if 'kafka_key' in request.POST else '',
    }
    if request.method == 'POST':

        if form_fields['mq'] == MQTypes.RabbitMQ:
            params = {
                "queue": form_fields['rabbit_queue'],     # queue
                "topic": form_fields['rabbit_topic'],     # topic
                "key": form_fields['rabbit_key'],     # key
            }
        elif form_fields['mq'] == MQTypes.Kafka:
            params = {
                "topic": form_fields['kafka_topic'],     # topic
                "key": form_fields['kafka_key'],     # key
            }
        else:
            raise Exception('Selected MQ "%s" is not supported' % form_fields['mq'])

    return form_fields, params