"""
This module contains the classes required to start various WSGI servers for the sake of a test.

FIXME: Some servers have shutdown code which will never be reached as the server is terminated with SIGTERM. This can be fixed by installing a SIGTERM handler or by sending SIGINT prior to SIGTERM.
"""

import sys
import os
import signal
import logging
import urllib2
import time
import warnings
import socket

from behaviours import wsgi_dispatcher
from errors import LabourException

servers = {}
def exposed(cls):
    servers[cls.__name__] = cls
    return cls

class ServerFailedToStart(LabourException):
    "Raised when we fail to receive a successful page delivery from the server during warmup time"

class Server(object):
    def __init__(self, interface='127.0.0.1', port=8000, do_warmup_wait=True):
        self.interface = interface
        self.port = port
        self.server_pid = None
        self.do_warmup_wait = do_warmup_wait
        self.logger = logging.getLogger('server.ctlr')
    def __str__(self):
        return self.__class__.__name__
    def __repr__(self):
        return '<%s on %s:%s>' % (self.__class__.__name__, self.interface, self.port,)
    @property
    def address(self):
        return (self.interface, self.port)
    def wait_until_warmup(self, iterations=10, delay=1):
        self.logger.info('waiting for server warm-up')
        for iteration in range(iterations):
            try:
                handle = urllib2.urlopen('http://%s:%s' %
                                         (self.interface, self.port))
                handle.read()
                handle.close()
                self.logger.info('server responds OK to requests')
                break
            except urllib2.URLError, error:
                if (not hasattr(error, 'reason') or
                    type(error.reason) is not socket.error):
                    self.logger.warning("caught unexpected %s during warm-up"
                                        " of server" %
                                        (error.__class__.__name__,))
                time.sleep(delay)
        else:
            self.shutdown()
            raise ServerFailedToStart('aborting, server failed to start',
                                      self.logger)
    def __enter__(self):
        self.logger.info('forking child process to run %s' % (self,))
        self.server_pid = os.fork()
        if self.server_pid == 0:
            try:
                self.logger = logging.getLogger('server.child')
                os.setsid()
                self.start()
            finally:
                # NOTE: we must exit here to make sure we never execute past
                #        the main function of the tested WSGI server
                os._exit(0)
        else:
            if self.do_warmup_wait:
                self.wait_until_warmup()
        return self
    def __exit__(self, error_type, error_value, traceback):
        self.shutdown()
    def shutdown(self):
        if self.server_pid is None:
            return
        self.logger.info('sending SIGTERM to server')
        os.kill(self.server_pid, signal.SIGTERM)
        self.server_pid = None
    def silence_spurious_logging(self, stdout=True, logger_names=()):
        # HACK: cruft to silences servers which spuriously write to stdout or 'import logging'
        if stdout:
            os.dup2(os.open('/dev/null', os.O_WRONLY), 1)
        for logger_name in logger_names:
            logging.getLogger(logger_name).setLevel(50)

@exposed
class WSGIRef(Server):
    def start(self):
        from wsgiref import simple_server

        class PimpedWSGIServer(simple_server.WSGIServer):
            # NOTE: increase the backlog
            request_queue_size = 500

        class PimpedHandler(simple_server.WSGIRequestHandler):
            # NOTE: disable logging
            def log_message(self, *args):
                pass

        httpd = PimpedWSGIServer((self.interface, self.port), PimpedHandler)
        httpd.set_app(wsgi_dispatcher)
        self.logger.info('%r serving forever...' % (self,))
        httpd.serve_forever()

@exposed
class Twisted(Server):
    def start(self):
        from twisted.web.server import Site
        from twisted.web.wsgi import WSGIResource
        from twisted.internet import reactor

        resource = WSGIResource(reactor, reactor.getThreadPool(), wsgi_dispatcher)
        reactor.listenTCP(self.port, Site(resource), interface=self.interface)
        self.logger.info('%r starting reactor...' % (self,))
        reactor.run()

@exposed
class CherryPy(Server):
    def start(self):
        from cherrypy import wsgiserver
        wsgi_apps = wsgiserver.WSGIPathInfoDispatcher([('/', wsgi_dispatcher)])
        server = wsgiserver.CherryPyWSGIServer((self.interface, self.port), wsgi_apps,
                                               request_queue_size=500, server_name=self.interface)
        self.logger.info('%r starting server...' % (self,))
        server.start()
        # FIXME: see module docstring
        server.stop()

@exposed
class Cogen(Server):
    def start(self):
        from cogen.web import wsgi
        from cogen.common import Scheduler, priority

        m = Scheduler(default_priority=priority.LAST, default_timeout=15)
        server = wsgi.WSGIServer(self.address, wsgi_dispatcher, m, server_name='Labour')
        m.add(server.serve)
        self.logger.info('%r running main loop...' % (self,))
        m.run()

class Concurrence(Server):
    # FIXME: for some reason this implementation returns 404, should be fixed later
    def start(self):
        from concurrence import dispatch
        from concurrence.http import WSGIServer
        server = WSGIServer(wsgi_dispatcher)
        self.logger.info('%r dispatching...' % (self,))
        dispatch(server.serve(self.address))

class Eventlet(Server):
    # FIXME: never tested, I had some difficulty installing eventlet, should be fixed later
    def start(self):
        import eventlet
        from eventlet import wsgi
        self.logger.info('%r starting...' % (self,))
        wsgi.server(eventlet.listen((self.address), backlog=500), wsgi_dispatcher, max_size=8000)

@exposed
class FAPWS3(Server):
    def start(self):
        import fapws._evwsgi as evwsgi
        from fapws import base

        self.silence_spurious_logging()

        evwsgi.start(self.interface, self.port)
        evwsgi.set_base_module(base)
        evwsgi.wsgi_cb(("/", wsgi_dispatcher))
        evwsgi.set_debug(0)
        self.logger.info('%r running...' % (self,))
        evwsgi.run()

@exposed
class Gevent(Server):
    def start(self):
        from gevent import wsgi
        self.logger.info('%r serving forever...' % (self,))
        self.silence_spurious_logging()
        # TODO: I didn't look much into spawn=None, it seems fitting since we already fork()ed
        #        but it best be looked into a tad more
        wsgi.WSGIServer(self.address, wsgi_dispatcher, spawn=None).serve_forever()

class Tornado(Server):
    # FIXME: never tested, I had some difficulty installing tornado, should be fixed later
    def start(self):
        import tornado.httpserver
        import tornado.ioloop
        import tornado.wsgi
        container = tornado.wsgi.WSGIContainer(wsgi_dispatcher)
        http_server = tornado.httpserver.HTTPServer(container)
        http_server.listen(self.port)
        self.logger.info('%r starting IO loop...' % (self,))
        tornado.ioloop.IOLoop.instance().start()

@exposed
class Paste(Server):
    def start(self):
        from paste import httpserver
        self.logger.info('%r serving...' % (self,))
        self.silence_spurious_logging(logger_names=('paste.httpserver.ThreadPool',))
        httpserver.serve(wsgi_dispatcher, '%s:%s' % (self.interface, self.port),
                         request_queue_size=500)

# TODO: remaining servers mentioned in Nicholas' original post: Aspen, Gunicorn, MagnumPy, Tornado, uWSGI and of course, mod_wsgi
