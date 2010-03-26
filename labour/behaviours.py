import sys
import inspect
import urlparse
import urllib
import time
import random
import signal
import os
import httplib

behaviours = {}
def behaviour(cls):
    behaviours[cls.__name__] = cls
    return cls

def wsgi_dispatcher(environ, start_response):
    # HACK: parsing the path manually here, the correct way is to use a something like python-routes
    behaviour_name = environ.get('PATH_INFO', '').strip('/').split('/')[0] or 'PlainResponse'
    behaviour_kwargs = urlparse.parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=False)
    behaviour = behaviours.get(behaviour_name, _NoSuchBehaviour)
    return behaviour.wsgi(environ, start_response, **behaviour_kwargs)

class Behaviour(object):
    @classmethod
    def make_plain_headers(cls, content_length):
        return [('Content-type', 'text/plain'), ('Content-Length', str(content_length))]
    def __init__(self, **kwargs):
        argspec = inspect.getargspec(self.wsgi)
        known_kwargs = argspec.args[-len(argspec.defaults):] if argspec.defaults is not None else []
        for kwarg in kwargs:
            if kwarg not in known_kwargs:
                raise TypeError("%s() got unexpected argument '%s'" % (self.__class__.__name__, kwarg))
        self.kwargs = kwargs
    def __str__(self):
        return "%s?%s" % (self.__class__.__name__, urllib.urlencode(self.kwargs))

class _NoSuchBehaviour(Behaviour):
    @classmethod
    def wsgi(cls, environ, start_response):
        output = 'Unknown behaviour requested\n'
        start_response(str(httplib.NOT_FOUND), cls.make_plain_headers(len(output)))
        yield output

@behaviour
class PlainResponse(Behaviour):
    @classmethod
    def wsgi(cls, environ, start_response, length=None, status=(httplib.OK,)):
        status = str(status[0])
        output = 'Pong!\n' if length is None else 'X' * int(length[0])
        start_response(status, cls.make_plain_headers(len(output)))
        yield output

@behaviour
class Sleeping(Behaviour):
    @classmethod
    def wsgi(cls, environ, start_response, sleep_duration=(1,)):
        sleep_duration = int(sleep_duration[0])
        outputs = ('Sleeping %s... ' % (sleep_duration,), 'and Pong!\n')
        start_response(str(httplib.OK), cls.make_plain_headers(sum(len(string) for string in outputs)))
        yield outputs[0]
        time.sleep(sleep_duration)
        yield outputs[1]

@behaviour
class IOBound(Behaviour):
    @classmethod
    def wsgi(cls, environ, start_response, filename=('/dev/zero',), length=(2**20,)):
        length = int(length[0])
        filename = filename[0]
        try:
            with file(filename) as file_handle:
                outputs = ('Reading %s bytes from %s... ' % (length, filename,), 'and Pong!\n')
                start_response(str(httplib.OK), cls.make_plain_headers(sum(len(string) for string in outputs)))
                yield outputs[0]
                # HACK: probably saner to read in blocks and discard them block after block, but whatever
                file_handle.read(length)
                yield outputs[1]
        except IOError, error:
            output = '%s: %s' % (filename, error.strerror)
            start_response(str(httplib.FORBIDDEN), cls.make_plain_headers(len(output)))
            yield output

@behaviour
class LeakMemory(Behaviour):
    @classmethod
    def wsgi(cls, environ, start_response, how_many=(1024,)):
        how_many = int(how_many[0])
        if not hasattr(sys, 'memory_leak'):
            sys.memory_leak = ''
        sys.memory_leak += 'X' * how_many
        output = 'Leaked %s bytes (%s bytes total). Pong!\n' % (how_many, len(sys.memory_leak))
        start_response(str(httplib.OK), cls.make_plain_headers(len(output)))
        yield output

@behaviour
class PythonWedge(Behaviour):
    @classmethod
    def wsgi(cls, environ, start_response):
        while True: pass
        output = 'Wedged. You should never see this.'
        start_response(str(httplib.OK), cls.make_plain_headers(len(output)))
        yield output

@behaviour
class SIGSEGV(Behaviour):
    @classmethod
    def wsgi(cls, environ, start_response):
        # HACK: raising SIGSEGV is lazy, I gather Bicking meant I'd /really/ segfault...
        #        I'm not certain a 'real' segfault will be a better test, but it prolly not too bad an idea to implement
        os.kill(os.getpid(), signal.SIGSEGV)
        output = 'Raised SIGSEGV. You should never see this.'
        start_response(str(httplib.OK), cls.make_plain_headers(len(output)))
        yield output
