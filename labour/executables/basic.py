import sys
import argparse
import httplib

from labour import servers
from labour import client
from labour import behaviours
from labour import reports

def main(argv):
    print("Running basic test against WSGIRef.")
    driver = client.Client()
    driver.add(behaviours.PlainResponse(), weight=98)
    driver.add(behaviours.Sleeping(sleep_duration=0.5), weight=1)
    driver.add(behaviours.PlainResponse(status=httplib.INTERNAL_SERVER_ERROR),
               weight=1)

    with servers.WSGIRef() as server:
        result = driver.execute(iterations=512)

    reports.PlainReport(result).emit('ascii')
