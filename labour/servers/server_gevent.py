from gevent import wsgi

from base import Server, wsgi_dispatcher

class Gevent(Server):
    def start(self):
        self.logger.info('%r serving forever...' % (self,))
        self.silence_spurious_logging()
        # TODO: I didn't look much into what spawn=None means, it seems
        #        fitting since we already fork()ed but it best be checked
        wsgi.WSGIServer(self.address, wsgi_dispatcher, spawn=None).serve_forever()
