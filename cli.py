#!/usr/bin/env python

import sys
import argparse
import httplib
from multiprocessing import cpu_count
import logging

from labour.servers import servers as servers_map
from labour import client
from labour import behaviours
from labour import report
from labour import log
from labour.errors import main_error_handler

def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', choices=servers_map, default='WSGIRef')
    parser.add_argument('-i', '--iterations', type=int, default=512)
    parser.add_argument('-p', '--number-processes', type=int, default=cpu_count())
    log.add_argparse_verbosity_options(parser)
    options = parser.parse_args(argv)
    options.server = servers_map[options.server]
    return options

@main_error_handler
def main(argv):
    options = parse_arguments(argv[1:])
    log.setup_logging(options)

    driver = client.Client()
    driver.add(behaviours.PlainResponse(), weight=98)
    driver.add(behaviours.Sleeping(sleep_duration=0.5), weight=1)
    driver.add(behaviours.PlainResponse(status=httplib.INTERNAL_SERVER_ERROR),
               weight=1)

    with options.server() as server:
        statistics, duration = \
            driver.execute(iterations=options.iterations,
                           number_processes=options.number_processes)

    report.PlainReport(statistics, duration).emit('ascii')

if __name__ == '__main__':
    main(sys.argv)
