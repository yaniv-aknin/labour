"""Responses objects aggregate the information gathered from all the
HTTP responses received from the server so far."""

import urllib2
import socket
import httplib

from ..http_hit import SUCCESS

class Responses(object):
    """Responses objects aggregate the information gathered from all the
    HTTP responses received from the server so far.
    
    Responses objects can be added to one another; this feature is used
    to combine the Responses' objects received from several child
    processes into a single Responses objects to pass to reporting."""
    def __init__(self):
        self.total_requests = 0
        self.response_histogram = {}
    def success(self):
        self.total_requests += 1
    def failure(self, error):
        """A long and tedious method, mostly dictated by urllib2's
        horrors, which receives an exception instance and stores
        a reasonably canonical error message/code in a histogram
        of errors that occured."""
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
