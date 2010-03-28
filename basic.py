#!/usr/bin/env python

import sys
import argparse
import httplib

from labour import servers
from labour import client
from labour import behaviours
from labour import report

driver = client.Client()
driver.add_behaviour(behaviours.PlainResponse(), weight=99)
driver.add_behaviour(behaviours.Sleeping(sleep_duration=0.5), weight=1)

with servers.WSGIRef as server:
    driver.execute(iterations=options.iterations)

report.trivial_report(driver)
