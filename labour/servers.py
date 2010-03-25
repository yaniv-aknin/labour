import os
import signal

from labour.behaviours import wsgi_dispatcher

class Server(object):
    pass

class PythonServer(Server):
    def __init__(self):
        super(PythonServer, self).__init__()
        self.server_pid = None
    def __enter__(self):
        self.server_pid = os.fork()
        if self.server_pid == 0:
            os.setsid()
            self.start()
        return self
    def __exit__(self, error_type, error_value, traceback):
        if self.server_pid is None:
            return
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

        httpd = PimpedWSGIServer(('',8000), PimpedHandler)
        httpd.set_app(wsgi_dispatcher)
        httpd.serve_forever()
