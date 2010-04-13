import tornado.httpserver
import tornado.ioloop
import tornado.wsgi

from base import Server, wsgi_dispatcher

class Tornado(Server):
    def start(self):
        container = tornado.wsgi.WSGIContainer(wsgi_dispatcher)
        # HACK: I found no other way to silence logging for this server,
        #        it's seems like the development version currently on github
        #        is better in this regard
        container._log = lambda status_code, request: None
        http_server = tornado.httpserver.HTTPServer(container)
        http_server.listen(self.port)
        self.logger.info('%r starting IO loop...' % (self,))
        tornado.ioloop.IOLoop.instance().start()
