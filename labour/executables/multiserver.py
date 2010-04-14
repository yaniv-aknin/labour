from __future__ import print_function

import sys
import argparse
import httplib
from multiprocessing import cpu_count

from labour import servers
from labour.servers import servers as servers_map
from labour import client
from labour import behaviours
from labour import reports
from labour.errors import main_error_handler

@main_error_handler
def main(argv):
    options = parse_arguments(argv[1:])

    test_cases = make_test_cases()
    report = reports.TableReport(test_names=test_cases)

    for server_class in options.servers:
        server_results = []
        print("%s undergoing test: " % server_class.__name__, end="")
        prefix = ''
        for test_name, test_case in test_cases.items():
            print("%s%r" % (prefix, test_name), end="")
            prefix = ', '
            sys.stdout.flush()
            with server_class() as server:
                server_results.append(
                    test_case.execute(iterations=options.iterations,
                                      number_processes=options.number_processes)
                )
        print(".")
        report.add_results(server_class.__name__, server_results)

    report.emit('ascii')

def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s', '--servers', choices=servers_map, action='append', default=[],
        help="Choose servers to run against (default: all)"
    )
    parser.add_argument('-i', '--iterations', type=int, default=100,
                        help="How many requests to issue per server per test")
    parser.add_argument('-p', '--number-processes', type=int, default=cpu_count(),
                        help="How many request-generators to fork in parallel")
    options = parser.parse_args(argv)
    if not options.servers:
        options.servers = servers_map.values()
    else:
        options.servers = [servers_map[server_name] for
                           server_name in options.servers]
    return options

def make_test_cases():
    # HACK: I want Ubuntu Claus to bring me Python 2.7 installed by default...
    try:
        from collections import OrderedDict as mapping_class
    except ImportError:
        mapping_class = dict
    result = mapping_class()
    result["Plain"] = client.Client.from_behaviour_tuples(
            (behaviours.PlainResponse(), 99),
            (behaviours.PlainResponse(status=httplib.NOT_FOUND), 1)
    )
    result["Light Sleep"] = client.Client.from_behaviour_tuples(
            (behaviours.PlainResponse(), 99),
            (behaviours.Sleeping(sleep_duration=0.5), 1),
    )
    result["Heavy Sleep"] = client.Client.from_behaviour_tuples(
            (behaviours.PlainResponse(), 95),
            (behaviours.Sleeping(sleep_duration=2), 5),
    )
    result["SIGSEGV"] = client.Client.from_behaviour_tuples(
                (behaviours.PlainResponse(), 50),
                (behaviours.SIGSEGV(), 50),
    )
    return result
