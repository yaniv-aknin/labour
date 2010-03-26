#!/usr/bin/env python

import sys
import argparse

from labour import servers
from labour.servers import servers as servers_map
from labour import client
from labour import behaviours
from labour import report
from labour import log as log
from labour.errors import main_error_handler

def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', choices=servers_map, default='WSGIRef')
    options = parser.parse_args(argv)
    options.server = servers_map[options.server]
    return options

@main_error_handler
def main(argv):
    log.setup_logging()
    options = parse_arguments(argv[1:])

    with options.server() as server:
        driver = client.Client()
        driver.add_behaviour(behaviours.PlainResponse(), weight=99)
        driver.add_behaviour(behaviours.Sleeping(sleep_duration=5), weight=1)

        driver.execute(iterations=128)

    report.trivial_report(driver)

if __name__ == '__main__':
    main(sys.argv)
