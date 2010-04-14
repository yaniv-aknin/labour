import random
import time
import urllib2
import httplib
import logging
import os
import socket
from collections import namedtuple

from labour.multicall import multicall
from labour.http_hit import hit, SUCCESS

Result = namedtuple("Result", "responses, duration")

LOGGER = logging.getLogger('client')

class Responses(object):
    def __init__(self):
        self.total_requests = 0
        self.response_histogram = {}
    def success(self):
        self.total_requests += 1
    def failure(self, error):
        self.total_requests += 1
        # CRUFT: Slowly hack away at the exception into something we
        #               can put in a histogram what a piece of shit.
        if error is SUCCESS:
            error = 'unexpected successful response'
        elif isinstance(error, urllib2.HTTPError):
            error = str(error.code)
        elif isinstance(error, urllib2.URLError):
            error = error.reason
            if isinstance(error, socket.timeout):
                # NOTE: urlopen() times out with a URLError wrapping ai
                #       socket.timeout
                error = str(error)
            elif isinstance(error, socket.error):
                error = error.strerror
        elif isinstance(error, httplib.HTTPException):
            error = error.__class__.__name__
        elif isinstance(error, socket.timeout):
            # NOTE: adinfourl.read() times out with a bare socket.timeout
            error = str(error)
        else:
            raise TypeError("%s is not a known error type"
                            % error.__class__)
        if error not in self.response_histogram:
            self.response_histogram[error] = 0
        self.response_histogram[error] += 1
    @property
    def successes(self):
        return self.total_requests - self.failures
    @property
    def failures(self):
        return sum(self.response_histogram.values())
    def __add__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        result = Responses()
        result.total_requests = self.total_requests + other.total_requests
        result.response_histogram = dict(self.response_histogram)
        self._sum_update(result.response_histogram, other.response_histogram)
        return result
    def __iadd__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        self.total_requests += other.total_requests
        self._sum_update(self.response_histogram, other.response_histogram)
        return self
    @staticmethod
    def _sum_update(map1, map2):
        for key, value in map2.items():
            if key not in map1:
                map1[key] = 0
            map1[key] += value

class Client(object):
    def __init__(self, host='localhost', port=8000, timeout_seconds=30):
        self.host = host
        self.port = port
        self.timeout_seconds = 30
        self.responses = Responses()
        self.behaviours = []
    @classmethod
    def from_behaviour_tuples(cls, *behaviour_tuples, **kwargs):
        result = cls(**kwargs)
        for behaviour, weight in behaviour_tuples:
            result.add(behaviour, weight)
        return result
    @property
    def base(self):
        return 'http://%s:%s' % (self.host, self.port,)
    def add(self, behaviour, weight):
        self.behaviours.extend([behaviour]*weight)
    def divide_iterations(self, iterations, number_processes):
        if iterations < number_processes or iterations % number_processes != 0:
            raise ValueError('can not divide %d iterations between %d processes')
        return iterations / number_processes
    def execute(self, iterations=1, number_processes=1):
        child_iterations = self.divide_iterations(iterations, number_processes)
        LOGGER.info('generating %s requests using %d processes' %
                    (iterations, number_processes))
        start_time = time.time()
        results = multicall(self._execute, (child_iterations,),
                            how_many=number_processes)
        duration = time.time() - start_time
        self.responses = sum(results, self.responses)
        LOGGER.info('finished all requests')
        return Result(self.responses, duration)
    def _execute(self, iterations):
        # NOTE: this will run in a child process
        global LOGGER
        # NOTE: reseed RNG, so not all kids will use parent's seed
        random.seed()
        LOGGER = logging.getLogger('client.%d' % (os.getpid(),))
        LOGGER.debug('running %d iterations' % (iterations,))
        responses = Responses()
        for iteration in xrange(iterations):
            # HACK: use proper url joining
            behaviour = random.choice(self.behaviours)
            result = hit(self.base + '/' + str(behaviour),
                         timeout=behaviour.timeout)
            if behaviour.is_expected_response(result):
                responses.success()
            else:
                responses.failure(result)
        return responses
