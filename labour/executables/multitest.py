from __future__ import print_function

import sys
import argparse
import httplib
from multiprocessing import cpu_count

from labour import servers
from labour import tester
from labour import reports
from labour.errors import main_error_handler

@main_error_handler
def main(argv):
    options = parse_arguments(argv[1:])

    test_mapping = create_test_client_mapping(options, *options.tests)
    report = reports.TableReport(test_names=test_mapping)

    for server_class in options.servers:
        server_results = []
        print("%s undergoing test: " % server_class.__name__, end="")
        prefix = ''
        for test_name, client in test_mapping.items():
            print("%s%r" % (prefix, test_name), end="")
            prefix = ', '
            sys.stdout.flush()
            with server_class() as server:
                server_results.append(client.execute(
                        iterations=options.iterations,
                        number_processes=options.number_processes
                    )
                )
        print(".")
        report.add_results(server_class.__name__, server_results)

    report.emit('ascii')

def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s', '--servers', action=servers.cli.MultiServerChoice, default=[],
        help="Choose servers to run against (default: all)"
    )
    parser.add_argument('-i', '--iterations', type=int, default=128,
                        help="How many requests to issue per server per test")
    parser.add_argument('-p', '--number-processes', type=int, default=cpu_count(),
                        help="How many request-generators to fork in parallel")
    parser.add_argument(
        '-t', '--tests', action=tester.cli.MultiTestChoice, default=[],
        help="Choose tests to run (default: all)"
    )
    options = parser.parse_args(argv)
    if not options.servers:
        options.servers = servers.server_map.values()
    if not options.tests:
        options.tests = tester.factories.test_factory_map
    return options
"Plain", "LightSleep", "HeavySleep", "SIGSEGV",

def create_test_client_mapping(options, *test_factory_names):
    result = {}
    for name in test_factory_names:
        client_factory = getattr(tester.factories, name)
        result[name] = client_factory()
    return result
