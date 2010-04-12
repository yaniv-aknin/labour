from __future__ import print_function

import sys
from functools import partial

class BaseReport(object):
    def emit(self, format, file=sys.stdout):
        try:
            emit_function = getattr(self, '_emit_%s' % (format,))
        except AttributeError, error:
            raise NotImplementedError('%s does not support emitting as %s' %
                                      (self, format))
        return emit_function(file)

class PlainReport(BaseReport):
    def __init__(self, statistics, duration):
        self.statistics = statistics
        self.duration = duration
    def _emit_ascii(self, file):
        statistics = self.statistics
        _print = partial(print, file=file)
        _print("\nTest of %d requests complete in %.2f seconds (%.2freq/s)." %
               (self.statistics.total_requests, self.duration,
                self.statistics.total_requests / self.duration))
        success_percentage = (float(self.statistics.successes) /
                              self.statistics.total_requests * 100)
        failure_percentage = (float(self.statistics.failures) /
                              self.statistics.total_requests * 100)
        _print("%d requests (%.2f%%) returned OK and %d (%.2f%%) failed."
               % (self.statistics.successes, success_percentage,
                  self.statistics.failures, failure_percentage))
        _print()
        if self.statistics.failures:
            _print("Failure Breakdown:")
            for status, amount in self.statistics.response_histogram.items():
                _print("Code: %s\tCount: %d\tPercentage: %.2f%%" %
                       (status, amount,
                        float(amount) / self.statistics.failures * 100))
