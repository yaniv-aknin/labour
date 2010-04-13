from concurrence import dispatch
from concurrence.http import WSGIServer

from base import Server, wsgi_dispatcher

class Concurrence(Server):
    # FIXME: for some reason this implementation returns 404, should be fixed later
    def start(self):
        server = WSGIServer(wsgi_dispatcher)
        self.logger.info('%r dispatching...' % (self,))
        dispatch(server.serve(self.address))
