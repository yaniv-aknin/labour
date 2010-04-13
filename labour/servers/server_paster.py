from paste import httpserver

from base import Server, wsgi_dispatcher

class Paster(Server):
    def start(self):
        self.logger.info('%r serving...' % (self,))
        self.silence_spurious_logging(logger_names=('paste.httpserver.ThreadPool',))
        httpserver.serve(wsgi_dispatcher, '%s:%s' % (self.interface, self.port),
                         request_queue_size=500)
