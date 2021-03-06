"""Various utility functions for choosing a server from the known
server map using argparse Actions."""

import argparse

from ..servers import server_map
from ..servers import supported_servers

def print_server_list():
    print("Supported servers:")
    for server_name in supported_servers:
        print("    %s %s" %
             ("+" if server_name in server_map else "-", server_name,))
    print("(servers marked with '+' are available on this system)")

class ServerChoice(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        if value == 'list':
            print_server_list()
            raise SystemExit(0)
        if value not in server_map:
            parser.error("%s is not a supported server;"
                         " use '%s list' for a list" %
                         (value, option_string))
        self._update_namespace(namespace, value)
    def _update_namespace(self, namespace, value):
        setattr(namespace, self.dest, server_map[value])

class MultiServerChoice(ServerChoice):
    def _update_namespace(self, namespace, value):
        getattr(namespace, self.dest).append(server_map[value])
