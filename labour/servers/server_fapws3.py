# BROKEN: At the time of this writing (Apr 2010), I believe FAPWS3
#          version 0.4 does not comply with the WSGI protocol correctly
#          and therefore is not supported by Labour.
#         See http://github.com/william-os4y/fapws3/issues/issue/8

import fapws._evwsgi as evwsgi
from fapws import base

from base import Server, wsgi_dispatcher

class FAPWS3(Server):
    def start(self):
        self.silence_spurious_logging()

        evwsgi.start(self.interface, self.port)
        evwsgi.set_base_module(base)
        evwsgi.wsgi_cb(("/", wsgi_dispatcher))
        evwsgi.set_debug(0)
        self.logger.info('%r running...' % (self,))
        evwsgi.run()

