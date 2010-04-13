from twisted.web.server import Site
from twisted.web.wsgi import WSGIResource
from twisted.internet import reactor

from base import Server, wsgi_dispatcher

class Twisted(Server):
    def start(self):
        resource = WSGIResource(reactor, reactor.getThreadPool(), wsgi_dispatcher)
        reactor.listenTCP(self.port, Site(resource), interface=self.interface)
        self.logger.info('%r starting reactor...' % (self,))
        reactor.run()
