import tornado.httpserver
import tornado.ioloop
import tornado.wsgi

from base import Server, wsgi_dispatcher

class Tornado(Server):
    # FIXME: never tested, I had some difficulty installing tornado, should be fixed later
    def start(self):
        container = tornado.wsgi.WSGIContainer(wsgi_dispatcher)
        http_server = tornado.httpserver.HTTPServer(container)
        http_server.listen(self.port)
        self.logger.info('%r starting IO loop...' % (self,))
        tornado.ioloop.IOLoop.instance().start()

