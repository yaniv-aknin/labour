from __future__ import print_function

import sys
from functools import partial

class BaseReport(object):
    def __init__(self, *data):
        self.data = data
    def feed(self, datum):
        self.data.append(datum)
    def emit(self, format, file=sys.stdout):
        try:
            emit_function = getattr(self, '_emit_%s' % (format,))
        except AttributeError, error:
            raise NotImplementedError('%s does not support emitting as %s' %
                                      (self, format))
        return emit_function(file)

class PlainReport(BaseReport):
    def feed(self, datum):
        if self.data:
            raise ValueError("%s can only be fed once" % (self,))
        super(PlainReport, self).feed(datum)
    def _emit_ascii(self, file):
        statistics = self.data[0]
        _print = partial(print, file=file)
        _print("\nTest complete.")
        success_percentage = (float(statistics.successes) /
                              statistics.total_requests * 100)
        failure_percentage = (float(statistics.failures) /
                              statistics.total_requests * 100)
        _print("Total requests sent: %d (%d (%.2f%%) returned OK and %d"
               " (%.2f%%) had some failure." %
               (statistics.total_requests, statistics.successes,
                success_percentage, statistics.failures, failure_percentage))
        _print()
        if statistics.failures:
            _print("Failure Breakdown:")
            for status, amount in statistics.response_histogram.iteritems():
                _print("Code: %s\tCount: %d\tPercentage: %.2f%%" %
                       (status, amount,
                        float(amount) / statistics.failures * 100))
