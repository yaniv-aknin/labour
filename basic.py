#!/usr/bin/env python

import sys

from labour import servers
from labour import client
from labour import behaviours
from labour import report
from labour import log as log
from labour.errors import main_error_handler

@main_error_handler
def main(argv):
    log.setup_logging()

    with servers.WSGIRef() as server:
        driver = client.Client()
        driver.add_behaviour(behaviours.PlainResponse(), weight=99)
        driver.add_behaviour(behaviours.Sleeping(sleep_duration=5), weight=1)

        driver.execute(iterations=128)

    report.trivial_report(driver)

if __name__ == '__main__':
    main(sys.argv)
