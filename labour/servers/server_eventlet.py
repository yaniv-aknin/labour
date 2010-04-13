import eventlet
from eventlet import wsgi

from base import Server, wsgi_dispatcher

class Eventlet(Server):
    # FIXME: never tested, I had some difficulty installing eventlet, should be fixed later
    def start(self):
        self.logger.info('%r starting...' % (self,))
        wsgi.server(eventlet.listen((self.address), backlog=500), wsgi_dispatcher, max_size=8000)
