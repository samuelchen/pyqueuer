#!/usr/bin/env python
# coding: utf-8

from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate
from pyqueuer.models import UserConf, ConfKeys
import sys
import getpass


class Command(BaseCommand):
    def add_arguments(self, parser):

        parser.add_argument(
            '--list', '-l',
            action='store_true',
            dest='list',
            default=False,
            help='List all personal settings of current user.',
        )

        parser.add_argument(
            '--password', '-p',
            action='store',
            type=str,
            dest='password',
            help='User password to login. If not specified, will prompt to enter.',
        )

        parser.add_argument(
            '--user', '-u',
            action='store',
            type=str,
            dest='user',
            help='User name to login. Must be specified.',
        )

        parser.add_argument(
            '--get', '-g',
            action='store',
            type=str,
            dest='get',
            help='Get the value for given option.',
        )

        parser.add_argument(
            'conf',
            nargs='*',
            type=str,
            metavar='option',
            help='Setting options "key=value [key1=value1 ...]" (no space around "=").',
        )

    def handle(self, *args, **options):
        name = options['user']
        pwd = options['password']
        show_list = options['list']
        conf = options['conf']
        key = options['get']

        if not name:
            name = input('Please enter your user name:')

        if not pwd:
            pwd = getpass.getpass('Please enter the password for user "%s" :' % name)

        user = authenticate(username=name, password=pwd)
        if user and user.is_active:
            pass
        else:
            sys.stderr.write('You are not authorized with given user name and password.\r\n')
            return

        ucf = UserConf(user=user)
        sb = []
        if show_list:
            # show config list
            if conf:
                print('Ignore all options due to "--list" specified.')

            for opt in ucf.all():
                sb.append('%s=%s' % (opt.name, opt.value))
            return '\r\n'.join(sb)

        elif conf:
            # set configurations
            opts = []
            for token in conf:
                opt = token.split('=')
                if len(opt) != 2:
                    # sys.stderr.write('Invalid syntax around "%s" \r\n' % token)
                    return 'Invalid syntax around "%s"' % token
                opt[0] = opt[0].strip()
                opts.append(opt)

            for opt in opts:
                is_valid = False
                for confs in ConfKeys.values():
                    if opt[0] in confs:
                        is_valid = True
                        break
                if is_valid:
                    ucf.set(opt[0], opt[1])
                else:
                    sys.stderr.write('"%s" is not a valid config name.' % opt[0])

        elif key:
            # get value of an config by given name
            return ucf.get(key)
        else:
            # sys.stderr.write('Please specify arguments such as --list or --get.\r\n')
            return 'Please specify arguments such as --list or --get.'

        return ''