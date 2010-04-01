import random
import signal
import urllib2
import urlparse
import logging

from labour import multicall

LOGGER = logging.getLogger('client')

class HTTPStatistics(object):
    def __init__(self):
        self.total_requests = 0
        self.response_histogram = {}
        self.unknown_exceptions = []
    def feed(self, error=None):
        self.total_requests += 1
        if not hasattr(error, 'code'):
            self.unknown_exceptions.append(error)
            return
        if error.code not in self.response_histogram:
            self.response_histogram[error.code] = 0
        self.response_histogram[error.code] += 1
    @property
    def successes(self):
        return self.total_requests - self.failures
    @property
    def failures(self):
        return sum(self.response_histogram.values())
    def __add__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        result = HTTPStatistics()
        result.total_requests = self.total_requests + other.total_requests
        result.response_histogram = dict(self.response_histogram)
        self._sum_update(result.response_histogram, other.response_histogram)
        result.unkown_exception = self.unknown_exceptions + other.unknown_exceptions
        return result
    def __iadd__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        self.total_requests += other.total_requests
        self._sum_update(self.response_histogram, other.response_histogram)
        self.unknown_exceptions += other.unknown_exceptions
        return self
    @staticmethod
    def _sum_update(map1, map2):
        for key, value in map2.items():
            if key not in map1:
                map1[key] = 0
            map1[key] += value

class Client(object):
    def __init__(self, host='localhost', port=8000):
        self.host = host
        self.port = port
        self.statistics = HTTPStatistics()
        self.behaviours = []
    def add_behaviour(self, behaviours, weight):
        self.behaviours.extend([behaviours]*weight)
    def execute(self, iterations=1):
        base = 'http://%s:%s' % (self.host, self.port,)
        LOGGER.info('Beginning %s requests against %s...' % (iterations, base))
        for iteration in xrange(iterations):
            try:
                self.hit(base + '/' + str(random.choice(self.behaviours)))
                self.statistics.feed()
            except urllib2.URLError, error:
                self.statistics.feed(error)
        LOGGER.info('Finished all requests.')
        return self.statistics
    def hit(self, url):
        handle = urllib2.urlopen(url)
        handle.read()
        handle.close()
