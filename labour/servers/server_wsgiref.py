from wsgiref import simple_server

from base import Server, wsgi_dispatcher

class WSGIRef(Server):
    def start(self):

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

