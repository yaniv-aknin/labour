import time
import sys
import argparse
import httplib

from labour import servers
from labour import tester
from labour import behaviours
from labour import reports
from labour import log
from labour.errors import main_error_handler

def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s', '--server', action=servers.cli.ServerChoice,
        help="Choose servers to run against (try 'list')",
        default=servers.WSGIRef
    )
    parser.add_argument(
        '-t', '--test', action=tester.cli.TestChoice,
        default='Plain', dest="test_name",
        help="Choose test to run (try: 'list')",
    )
    parser.add_argument('-i', '--iterations', type=int, default=128)
    parser.add_argument('-p', '--number-processes', type=int, default=1,
                        help="How many parallel test clients to spawn")
    parser.add_argument('-W', '--no-warmup', action="store_false",
                        dest="warmup", help="Don't wait for server to start"
                        " responding")
    parser.add_argument('-N', '--no-test', action="store_true",
                        help="Just run the server and block")
    parser.add_argument('-P', '--policy', choices=tester.policy_map,
                        help="Override test's Behaviour selection Policy",
                        dest="policy_override", default=None)
    log.add_argparse_verbosity_options(parser)
    options = parser.parse_args(argv)
    if options.policy_override in tester.policy_map:
        options.policy_override = tester.policy_map[options.policy_override]
    return options

@main_error_handler
def main(argv):
    options = parse_arguments(argv[1:])
    log.setup_logging(options)

    if options.no_test:
        run_server(options)
    else:
        run_test(options)

def run_server(options):
    with options.server(do_warmup=options.warmup):
        # NOTE: Give child time to log error messages before we
        #        marr stdout.
        time.sleep(0.5)
        raw_input("Hit [Return] to exit.")

def run_test(options):
    client_factory = getattr(tester.factories, options.test_name)
    if options.policy_override is not None:
        client_factory.kwargs["policy"] = options.policy_override
    client = client_factory()

    with options.server(do_warmup=options.warmup):
        result = client.execute(iterations=options.iterations,
                                number_processes=options.number_processes)

    reports.PlainReport(result).emit('ascii')
