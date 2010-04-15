"""Various utility functions for choosing a server from the known
server map using argparse Actions."""

import argparse

from factories import test_factory_map

def print_test_list():
    print("Supported tests:")
    for test_name, test in test_factory_map.items():
        print("  %s: %s" % (test_name, test.description,))

class MultiTestChoice(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        if value == 'list':
            print_test_list()
            raise SystemExit(0)
        if value not in test_factory_map:
            parser.error("no such test %r; use '%s list' for a list" %
                         (value, option_string))
        getattr(namespace, self.dest).append(value)
