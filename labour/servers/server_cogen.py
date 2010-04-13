from cogen.web import wsgi
from cogen.common import Scheduler, priority

from base import Server, wsgi_dispatcher

class Cogen(Server):
    def start(self):

        m = Scheduler(default_priority=priority.LAST, default_timeout=15)
        server = wsgi.WSGIServer(self.address, wsgi_dispatcher, m, server_name='Labour')
        m.add(server.serve)
        self.logger.info('%r running main loop...' % (self,))
        m.run()
