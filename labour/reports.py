from __future__ import print_function

import sys
from functools import partial
import warnings
try:
    import prettytable
except ImportError:
    warnings.warn("prettytable is not installed; will use dumb ascii output",
                  UserWarning)
    prettytable = None

DISQUALIFYING_FAILURE_PERCENTAGE = 10

class BaseReport(object):
    def get_request_rate(self, result):
        return result.responses.total_requests / result.duration
    def get_success_percentage(self, responses):
        return (float(responses.successes) / responses.total_requests * 100)
    def get_failure_percentage(self, responses):
        return (float(responses.failures) / responses.total_requests * 100)
    def emit(self, format, file=sys.stdout):
        try:
            emit_function = getattr(self, '_emit_%s' % (format,))
        except AttributeError, error:
            raise NotImplementedError('%s does not support emitting as %s' %
                                      (self, format))
        return emit_function(file)

class PlainReport(BaseReport):
    def __init__(self, result):
        self.result = result
    @property
    def responses(self):
        return self.result.responses
    @property
    def duration(self):
        return self.result.duration
    def _emit_ascii(self, file):
        request_rate = self.get_request_rate(self.result)
        success_percentage = self.get_success_percentage(self.responses)
        failure_percentage = self.get_failure_percentage(self.responses)
        _print = partial(print, file=file)
        _print("\nTest of %d requests complete in %.2f seconds (%.2freq/s)." %
               (self.responses.total_requests, self.duration, request_rate))
        _print("%d requests (%.2f%%) returned OK and %d (%.2f%%) failed."
               % (self.responses.successes, success_percentage,
                  self.responses.failures, failure_percentage))
        _print()
        if self.responses.failures:
            _print("Failure Breakdown:")
            for status, amount in self.responses.response_histogram.items():
                failure_percentage = (float(amount) /
                                      self.responses.failures * 100)
                _print("Code: %s\tCount: %d\tPercentage: %.2f%%" %
                       (status, amount, failure_percentage))

class TableReport(BaseReport):
    def __init__(self, test_names):
        self.test_names = test_names
        self.servers_results = {}
    def add_results(self, server_name, server_results):
        if len(server_results) != len(self.test_names):
            raise ValueError("expected %d items per row, got %d" %
                             (len(self.test_names), len(server_results)))
        if server_name in self.servers_results:
            raise ValueError("results for %s already added" % (server_name,))
        self.servers_results[server_name] = server_results
    def _emit_ascii(self, file):
        _print = partial(print, file=file)
        _print("\n%d test(s) against %d server(s) finished." %
               (len(self.test_names), len(self.servers_results)))
        _print("\nReport of request failure percent and requests/sec:")
        if prettytable is None:
            return self._emit_ugly_ascii(file)
        columns = ["Server"] + self.test_names
        table = prettytable.PrettyTable(columns)
        for column in columns:
            table.set_field_align(column, "l")
        for server_name, server_results in self.servers_results.items():
            row = [server_name]
            for result in server_results:
                row.append(self.format_result_tuple(result))
            table.add_row(row)
        print(table, file=file)
    def _emit_ugly_ascii(self, file):
        _print = partial(print, file=file)
        for test_number, test_name in enumerate(self.test_names):
            for server_name, server_results in self.servers_results.items():
                result = server_results[test_number]
                _print("Server: %s; Test: %s; Result: %s" %
                       (server_name, test_name,
                        self.format_result_tuple(result)))
    def format_result_tuple(self, result):
        failure_percentage = self.get_failure_percentage(result.responses)
        if failure_percentage > DISQUALIFYING_FAILURE_PERCENTAGE:
            return 'Failed'
        request_rate = self.get_request_rate(result)
        return "f%%: %.2f; RPS: %.2f" % (failure_percentage, request_rate)
