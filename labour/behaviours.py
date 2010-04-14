"Implementation of Behaviours; the heart of the Labour framework."

import sys
import inspect
import urlparse
import urllib
import urllib2
import time
import signal
import os
import httplib

import labour.http_hit

behaviours = {}
def behaviour(cls):
    behaviours[cls.__name__] = cls
    return cls

def wsgi_dispatcher(environ, start_response):
    """This is a plain dispatching function which extract the name of
    desired Behaviour as well as additional paramters from the HTTP
    Request. After the Behaviour returns (if at all, some Behaviours
    hang or kill the process), this function uses WSGI to return the
    result to the client."""
    # HACK: parsing the path manually here, the correct way is to use a
    #        something like python-routes
    first_path_element = environ.get('PATH_INFO', '').strip('/').split('/')[0]
    behaviour_name = first_path_element or 'PlainResponse'
    behaviour_kwargs = urlparse.parse_qs(environ.get('QUERY_STRING', ''),
                                         keep_blank_values=False)
    behaviour = behaviours.get(behaviour_name, _NoSuchBehaviour)
    return behaviour.wsgi(environ, start_response, **behaviour_kwargs)

class Behaviour(object):
    """Behaviours are dual-purpose classes which run both as part of the
    WSGI application under the WSGI Server as well as under the Client
    object which dispatches requests to test the server.

    When invoked inside the WSGI Application, Behaviours classes receive
    certain parameters from the HTTP request and perform some detrimental
    task (such as leaking resources or sleeping) prior to using the WSGI
    API in order to return an HTTP response to the client.
     -> See the 'wsgi' classmethod of Behaviours.

    Inside the Client Behaviour objects are instantiated with certain
    parameters which are then sent to the server as an HTTP request and
    affect the operation of the Behaviour inside the server. When the
    HTTP response returns from the server, the Behaviour instance which
    caused that HTTP response to be generated will validate that the
    response is as-expected.
    """
    DEFAULT_TIMEOUT = 30
    @staticmethod
    def make_plain_headers(content_length):
        return [('Content-type', 'text/plain'),
                ('Content-Length', str(content_length))]
    @staticmethod
    def make_http_status(code):
        return '%d %s' % (code, httplib.responses[code])
    def __init__(self, timeout=30, **kwargs):
        self.timeout = timeout
        argspec = inspect.getargspec(self.wsgi)
        if argspec.defaults is not None:
            known_kwargs = argspec.args[-len(argspec.defaults):]
        else:
            known_kwargs = []
        for kwarg in kwargs:
            if kwarg not in known_kwargs:
                raise TypeError("%s() got unexpected argument '%s'" %
                                (self.__class__.__name__, kwarg))
        self.kwargs = kwargs
    def __str__(self):
        return "%s?%s" % (self.__class__.__name__,
                          urllib.urlencode(self.kwargs))
    def is_expected_response(self, response):
        if response is labour.http_hit.SUCCESS:
            return True
        return False

class _NoSuchBehaviour(Behaviour):
    @classmethod
    def wsgi(cls, environ, start_response):
        output = 'Unknown behaviour requested\n'
        start_response(cls.make_http_status(httplib.NOT_FOUND),
                       cls.make_plain_headers(len(output)))
        yield output

@behaviour
class PlainResponse(Behaviour):
    @classmethod
    def wsgi(cls, environ, start_response, length=None, status=(httplib.OK,)):
        status = int(status[0])
        output = 'Pong!\n' if length is None else 'X' * int(length[0])
        start_response(cls.make_http_status(status),
                       cls.make_plain_headers(len(output)))
        yield output
    def is_expected_response(self, response):
        requested_http_status = self.kwargs.get('status', httplib.OK)
        if (requested_http_status == httplib.OK and
            response is labour.http_hit.SUCCESS):
            return True
        if (isinstance(response, urllib2.HTTPError) and
            response.code == requested_http_status):
            return True
        return False

@behaviour
class Sleeping(Behaviour):
    @classmethod
    def wsgi(cls, environ, start_response, sleep_duration=(1,)):
        sleep_duration = float(sleep_duration[0])
        outputs = ('Sleeping %s... ' % (sleep_duration,), 'and Pong!\n')
        start_response(cls.make_http_status(httplib.OK),
                       cls.make_plain_headers(sum(len(string) for
                                              string in outputs)))
        yield outputs[0]
        time.sleep(sleep_duration)
        yield outputs[1]

@behaviour
class IOBound(Behaviour):
    @classmethod
    def wsgi(cls, environ, start_response, filename=('/dev/zero',),
             length=(2**20,)):
        length = int(length[0])
        filename = filename[0]
        try:
            with file(filename) as file_handle:
                outputs = ('Reading %s bytes from %s... ' %
                           (length, filename,), 'and Pong!\n')
                start_response(cls.make_http_status(httplib.OK),
                               cls.make_plain_headers(sum(len(string) for
                                                      string in outputs)))
                yield outputs[0]
                # HACK: probably saner to read in blocks and discard them
                #       block after block, but whatever
                file_handle.read(length)
                yield outputs[1]
        except IOError, error:
            output = '%s: %s' % (filename, error.strerror)
            start_response(cls.make_http_status(httplib.FORBIDDEN),
                           cls.make_plain_headers(len(output)))
            yield output

@behaviour
class LeakMemory(Behaviour):
    @classmethod
    def wsgi(cls, environ, start_response, how_many=(1024,)):
        how_many = int(how_many[0])
        if not hasattr(sys, 'memory_leak'):
            sys.memory_leak = ''
        sys.memory_leak += 'X' * how_many
        output = ('Leaked %s bytes (%s bytes total). Pong!\n' %
                  (how_many, len(sys.memory_leak)))
        start_response(cls.make_http_status(httplib.OK),
                       cls.make_plain_headers(len(output)))
        yield output

@behaviour
class PythonWedge(Behaviour):
    @classmethod
    def wsgi(cls, environ, start_response):
        while True: pass
        output = 'Wedged. You should never see this.'
        start_response(cls.make_http_status(httplib.OK),
                       cls.make_plain_headers(len(output)))
        yield output
    def is_expected_response(self, response):
        # FIXME: not certain what's proper here, let's say anything of the
        #         server error range makes sense and anything else is wrong
        if (isinstance(response, urllib2.HTTPError) and
            response.code >= 500 and response < 600):
            return True
        return False

@behaviour
class SIGSEGV(Behaviour):
    @classmethod
    def wsgi(cls, environ, start_response):
        # HACK: raising SIGSEGV is lazy, I gather Bicking meant I'd /really/
        #        segfault... I'm not certain a 'real' segfault will be a
        #        better test, but didn't check that, either
        os.kill(os.getpid(), signal.SIGSEGV)
        output = 'Raised SIGSEGV. You should never see this.'
        start_response(cls.make_http_status(httplib.OK),
                       cls.make_plain_headers(len(output)))
        yield output
    def is_expected_response(self, response):
        # FIXME: not certain what's proper here, let's say anything of the
        #         server error range makes sense and anything else is wrong
        if (isinstance(response, urllib2.HTTPError) and
            response.code >= 500 and response < 600):
            return True
        return False
