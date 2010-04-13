from cherrypy import wsgiserver

from base import Server, wsgi_dispatcher

class CherryPy(Server):
    def start(self):
        wsgi_apps = wsgiserver.WSGIPathInfoDispatcher([('/', wsgi_dispatcher)])
        server = wsgiserver.CherryPyWSGIServer((self.interface, self.port), wsgi_apps,
                                               request_queue_size=500, server_name=self.interface)
        self.logger.info('%r starting server...' % (self,))
        server.start()
        # FIXME: this code will never be called... does this matter?
        server.stop()

