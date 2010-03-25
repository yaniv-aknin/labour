import sys
import inspect
import urlparse
import urllib
import time
import random
import signal
import os

STATUS_200 = '200 OK'
STATUS_403 = '403 Forbidden'
STATUS_404 = '404 Not Found'

behaviours = {}
def behaviour(cls):
    instance = cls()
    behaviours[cls.__name__] = instance
    return instance

def wsgi_dispatcher(environ, start_response):
    # HACK: parsing the path manually here, the correct way is to use a something like python-routes
    behaviour_name = environ.get('PATH_INFO', '').strip('/').split('/')[0] or 'PlainResponse'
    behaviour_kwargs = urlparse.parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=False)
    behaviour = behaviours.get(behaviour_name, _NoSuchBehaviour)
    return behaviour.wsgi(environ, start_response, **behaviour_kwargs)

class Behaviour(object):
    def make_plain_headers(self, content_length):
        return [('Content-type', 'text/plain'), ('Content-Length', str(content_length))]
    def __call__(self, **kwargs):
        argspec = inspect.getargspec(self.wsgi)
        known_kwargs = argspec.args[-len(argspec.defaults):] if argspec.defaults is not None else []
        for kwarg in kwargs:
            if kwarg not in known_kwargs:
                raise TypeError("%s() got unexpected argument '%s'" % (self.__class__.__name__, kwarg))
        return "%s?%s" % (self.__class__.__name__, urllib.urlencode(kwargs))

class _NoSuchBehaviour(Behaviour):
    def wsgi(self, environ, start_response):
        output = 'Unknown behaviour requested\n'
        start_response(STATUS_404, self.make_plain_headers(len(output)))
        yield output
_NoSuchBehaviour = _NoSuchBehaviour()

@behaviour
class PlainResponse(Behaviour):
    def wsgi(self, environ, start_response, length=None):
        output = 'Pong!\n' if length is None else 'X' * int(length[0])
        start_response(STATUS_200, self.make_plain_headers(len(output)))
        yield output

@behaviour
class Sleeping(Behaviour):
    def wsgi(self, environ, start_response, sleep_duration=(1,)):
        sleep_duration = int(sleep_duration[0])
        outputs = ('Sleeping %s... ' % (sleep_duration,), 'and Pong!\n')
        start_response(STATUS_200, self.make_plain_headers(sum(len(string) for string in outputs)))
        yield outputs[0]
        time.sleep(sleep_duration)
        yield outputs[1]

@behaviour
class IOBound(Behaviour):
    def wsgi(self, environ, start_response, filename=('/dev/zero',), length=(2**20,)):
        length = int(length[0])
        filename = filename[0]
        try:
            with file(filename) as file_handle:
                outputs = ('Reading %s bytes from %s... ' % (length, filename,), 'and Pong!\n')
                start_response(STATUS_200, self.make_plain_headers(sum(len(string) for string in outputs)))
                yield outputs[0]
                # HACK: probably saner to read in blocks and discard them block after block, but whatever
                file_handle.read(length)
                yield outputs[1]
        except IOError, error:
            output = '%s: %s' % (filename, error.strerror)
            start_response(STATUS_403, self.make_plain_headers(len(output)))
            yield output

@behaviour
class LeakMemory(Behaviour):
    def wsgi(self, environ, start_response, how_many=(1024,)):
        how_many = int(how_many[0])
        if not hasattr(sys, 'memory_leak'):
            sys.memory_leak = ''
        sys.memory_leak += 'X' * how_many
        output = 'Leaked %s bytes (%s bytes total). Pong!\n' % (how_many, len(sys.memory_leak))
        start_response(STATUS_200, self.make_plain_headers(len(output)))
        yield output

@behaviour
class PythonWedge(Behaviour):
    def wsgi(self, environ, start_response):
        while True: pass
        output = 'Wedged. You should never see this.'
        start_response(STATUS_200, self.make_plain_headers(len(output)))
        yield output

@behaviour
class SIGSEGV(Behaviour):
    def wsgi(self, environ, start_response):
        # HACK: raising SIGSEGV is lazy, I gather Bicking meant I'd /really/ segfault...
        #        I'm not certain a 'real' segfault will be a better test, but it prolly not too bad an idea to implement
        os.kill(os.getpid(), signal.SIGSEGV)
        output = 'Raised SIGSEGV. You should never see this.'
        start_response(STATUS_200, self.make_plain_headers(len(output)))
        yield output
