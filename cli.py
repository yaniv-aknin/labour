#!/usr/bin/env python

import time
import sys
import argparse
import httplib
from multiprocessing import cpu_count

from labour.servers import servers as servers_map
from labour import client
from labour import behaviours
from labour import reports
from labour import log
from labour.errors import main_error_handler

def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', choices=servers_map,
                        default='WSGIRef')
    parser.add_argument('-i', '--iterations', type=int, default=512)
    parser.add_argument('-p', '--number-processes', type=int,
                        default=cpu_count())
    parser.add_argument('-W', '--no-warmup', action="store_false",
                        dest="warmup", help="Don't wait for server to start"
                        " responding")
    parser.add_argument('-N', '--no-test', action="store_true",
                        help="Just run the server and block")
    log.add_argparse_verbosity_options(parser)
    options = parser.parse_args(argv)
    options.server = servers_map[options.server]
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
    driver = client.Client()
    driver.add(behaviours.PlainResponse(), weight=98)
    driver.add(behaviours.Sleeping(sleep_duration=0.5), weight=1)
    driver.add(behaviours.PlainResponse(status=httplib.INTERNAL_SERVER_ERROR),
               weight=1)

    with options.server(do_warmup=options.warmup):
        result = driver.execute(iterations=options.iterations,
                                number_processes=options.number_processes)

    reports.PlainReport(result).emit('ascii')

if __name__ == '__main__':
    main(sys.argv)
