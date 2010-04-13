import eventlet
from eventlet import wsgi

from base import Server, wsgi_dispatcher

class Eventlet(Server):
    def start(self):
        self.logger.info('%r starting...' % (self,))
        wsgi.server(eventlet.listen((self.address), backlog=500),
                    wsgi_dispatcher, max_size=8000,
                    log=self.silence_spurious_logging(stdout=False))
