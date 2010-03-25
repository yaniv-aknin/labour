import os
import signal
import logging

from labour.behaviours import wsgi_dispatcher

LOGGER = logging.getLogger('server')

class Server(object):
    def __init__(self, bind_address='127.0.0.1', port=8000):
        self.bind_address = bind_address
        self.port = port
    def __str__(self):
        return self.__class__.__name__
    def __repr__(self):
        return '<%s on %s:%s>' % (self.__class__.__name__, self.bind_address, self.port,)

class PythonServer(Server):
    def __init__(self):
        super(PythonServer, self).__init__()
        self.server_pid = None
    def __enter__(self):
        LOGGER.info('Forking child process to run %s.' % (self,))
        self.server_pid = os.fork()
        if self.server_pid == 0:
            os.setsid()
            self.start()
        return self
    def __exit__(self, error_type, error_value, traceback):
        if self.server_pid is None:
            return
        LOGGER.info('Sending SIGTERM to server.')
        os.kill(self.server_pid, signal.SIGTERM)

class WSGIRef(PythonServer):
    def start(self):
        from wsgiref import simple_server

        class PimpedWSGIServer(simple_server.WSGIServer):
            # To increase the backlog
            request_queue_size = 500

        class PimpedHandler(simple_server.WSGIRequestHandler):
            # to disable logging
            def log_message(self, *args):
                pass

        httpd = PimpedWSGIServer((self.bind_address, self.port), PimpedHandler)
        httpd.set_app(wsgi_dispatcher)
        LOGGER.info('%r serving forever...' % (self,))
        httpd.serve_forever()
