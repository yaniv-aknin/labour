from __future__ import print_function

import sys
import argparse
import httplib

from labour import servers
from labour import client
from labour import behaviours
from labour import reports

test_cases = {
    "Plain": client.Client.from_behaviour_tuples(
        (behaviours.PlainResponse(), 99),
        (behaviours.PlainResponse(status=httplib.NOT_FOUND), 1)
    ),
    "Light Sleep": client.Client.from_behaviour_tuples(
        (behaviours.PlainResponse(), 99),
        (behaviours.Sleeping(sleep_duration=0.5), 1),
    ),
    "Heavy Sleep": client.Client.from_behaviour_tuples(
        (behaviours.PlainResponse(), 95),
        (behaviours.Sleeping(sleep_duration=2), 5),
    ),
    "SIGSEGV": client.Client.from_behaviour_tuples(
            (behaviours.PlainResponse(), 50),
            (behaviours.SIGSEGV(), 50),
    )
}

server_classes = [servers.WSGIRef, servers.Paster]

report = reports.TableReport(test_names=test_cases.keys())

for server_class in server_classes:
    server_results = []
    for test_name, test_case in test_cases.items():
        with server_class() as server:
            print("Running %s against %s... " %
                  (test_name, server_class.__name__), end='')
            sys.stdout.flush()
            server_results.append(test_case.execute(iterations=100,
                                                    number_processes=2))
            print("Done")
    report.add_results(server_class.__name__, server_results)

report.emit('ascii')
