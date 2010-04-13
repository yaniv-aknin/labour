# BROKEN: At the time of this writing (Apr 2010), I believe Concurrence's
#          latest version (0.3.1) does not comply with the WSGI protocol
#          correctly and therefore is not supported by Labour.
#         See http://github.com/concurrence/concurrence/issues#issue/2

from concurrence import dispatch
from concurrence.http import WSGIServer

from base import Server, wsgi_dispatcher

class Concurrence(Server):
    def start(self):
        server = WSGIServer(wsgi_dispatcher)
        self.logger.info('%r dispatching...' % (self,))
        dispatch(server.serve(self.address))

