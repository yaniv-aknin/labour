#!/usr/bin/env python

import sys
import argparse
import httplib

from labour import servers
from labour import client
from labour import behaviours
from labour import report

driver = client.Client()
driver.add_behaviour(behaviours.PlainResponse(), weight=98)
driver.add_behaviour(behaviours.Sleeping(sleep_duration=0.5), weight=1)
driver.add_behaviour(behaviours.PlainResponse(status=httplib.INTERNAL_SERVER_ERROR), weight=1)

with servers.WSGIRef() as server:
    statistics = driver.execute(iterations=512)

report.PlainReport(statistics).emit('ascii')
