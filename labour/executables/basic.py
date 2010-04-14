import sys
import argparse
import httplib

from labour import servers
from labour import tester
from labour import behaviours
from labour import reports

def main(argv):
    print("Running basic test against WSGIRef.")
    client = tester.Client()
    client.add(behaviours.PlainResponse(), weight=98)
    client.add(behaviours.Sleeping(sleep_duration=0.5), weight=1)
    client.add(behaviours.PlainResponse(status=httplib.INTERNAL_SERVER_ERROR),
               weight=1)

    with servers.WSGIRef() as server:
        result = client.execute(iterations=512)

    reports.PlainReport(result).emit('ascii')
