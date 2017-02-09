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
            help='User name to login. If not specified, will prompt to enter.',
        )

        parser.add_argument(
            '--get', '-g',
            action='store',
            type=str,
            dest='get',
            help='Get the value for given option.',
        )

        parser.add_argument(
            '--import', '-i',
            action='store',
            type=str,
            dest='imp',
            help='Import user configs from file. Format same as --list. (use --list>file to generate).',
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
        imp = options['imp']

        if not name:
            name = input('Please enter your user name:')

        if not pwd:
            pwd = getpass.getpass('Please enter the password for user "%s" :' % name)

        user = authenticate(username=name, password=pwd)
        if user and user.is_active:
            pass
        else:
            # sys.stderr.write('You are not authorized with given user name and password.\r\n')
            return 'You are not authorized with given user name and password.'

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
            return self.set_configs(user=user, tokens=conf)

        elif key:
            # get value of an config by given name
            return ucf.get(key)
        elif imp:
            # import from file.
            try:
                with open(imp, 'rt') as f:
                    return self.set_configs(user=user, tokens=f.readlines())
            except (FileNotFoundError, PermissionError, FileExistsError):
                return 'File is not accessible.'

        else:
            # sys.stderr.write('Please specify arguments such as --list or --get.\r\n')
            return 'Please specify arguments such as --list or --get.'

        return ''

    @staticmethod
    def set_configs(user, tokens):
        ucf = UserConf(user=user)
        opts = []
        for token in tokens:
            token = token.strip()
            if not token:
                continue
            opt = token.split('=')
            if len(opt) != 2:
                return 'Invalid syntax around "%s"' % token
            opt[0] = opt[0].strip()
            opt[1] = opt[1].strip()
            opts.append(opt)

        for opt in opts:
            is_valid = False
            for confs in ConfKeys.values():
                if opt[0] in confs.values():
                    is_valid = True
                    break
            if is_valid:
                ucf.set(opt[0], opt[1])
            else:
                sys.stderr.write('"%s" is not a valid config name.\r\n' % opt[0])

        return 'Configuration modified.'
