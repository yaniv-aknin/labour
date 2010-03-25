import os
import signal
import logging
import urllib2
import time

from behaviours import wsgi_dispatcher
from errors import LabourException

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
    def wait_until_warmup(self, iterations=10, delay=1):
        self.logger.info('Waiting for server warm-up...')
        for iteration in range(iterations):
            try:
                handle = urllib2.urlopen('http://%s:%s' % (self.interface, self.port))
                handle.read()
                handle.close()
                self.logger.info('Server responds OK to requests.')
                break
            except urllib2.URLError:
                time.sleep(delay)
        else:
            self.shutdown()
            raise ServerFailedToStart('Server failed to start. Aborting.', self.logger)
    def __enter__(self):
        self.logger.info('Forking child process to run %s.' % (self,))
        self.server_pid = os.fork()
        if self.server_pid == 0:
            self.logger = logging.getLogger('server.child')
            os.setsid()
            self.start()
        else:
            if self.do_warmup_wait:
                self.wait_until_warmup()
        return self
    def __exit__(self, error_type, error_value, traceback):
        self.shutdown()
    def shutdown(self):
        if self.server_pid is None:
            return
        self.logger.info('Sending SIGTERM to server.')
        os.kill(self.server_pid, signal.SIGTERM)
        self.server_pid = None

class WSGIRef(Server):
    def start(self):
        from wsgiref import simple_server

        class PimpedWSGIServer(simple_server.WSGIServer):
            # To increase the backlog
            request_queue_size = 500

        class PimpedHandler(simple_server.WSGIRequestHandler):
            # to disable logging
            def log_message(self, *args):
                pass

        httpd = PimpedWSGIServer((self.interface, self.port), PimpedHandler)
        httpd.set_app(wsgi_dispatcher)
        self.logger.info('%r serving forever...' % (self,))
        httpd.serve_forever()
        raise SystemExit(0)

class Twisted(Server):
    def start(self):
        from twisted.web.server import Site
        from twisted.web.wsgi import WSGIResource
        from twisted.internet import reactor

        resource = WSGIResource(reactor, reactor.getThreadPool(), wsgi_dispatcher)
        reactor.listenTCP(self.port, Site(resource), interface=self.interface)
        self.logger.info('%r starting reactor...' % (self,))
        reactor.run()
        raise SystemExit(0)
