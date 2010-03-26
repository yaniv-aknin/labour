import random
import signal
import urllib2
import urlparse
import logging

LOGGER = logging.getLogger('client')

class Client(object):
    def __init__(self, host='localhost', port=8000):
        self.host = host
        self.port = port
        self.behaviours = []
        self.successes = 0
        self.failures = 0
        self.received_statuses = {}
    def add_behaviour(self, behaviours, weight):
        self.behaviours.extend([behaviours]*weight)
    def execute(self, iterations=1):
        base = 'http://%s:%s' % (self.host, self.port,)
        LOGGER.info('Beginning %s requests against %s...' % (iterations, base))
        for iteration in xrange(iterations):
            try:
                url = base + '/' + str(random.choice(self.behaviours))
                handle = urllib2.urlopen(url)
                handle.read()
                handle.close()
                self.successes += 1
            except urllib2.URLError, error:
                self.failures += 1
                if error.code not in self.received_statuses:
                    self.received_statuses[error.code] = 0
                self.received_statuses[error.code] += 1
        LOGGER.info('Finished all requests.')
