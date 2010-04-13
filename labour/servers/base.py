"""
This module contains the classes required to start various WSGI servers
for the sake of a test.

FIXME: Some servers have shutdown code which will never be reached as
the server is terminated with SIGTERM. This can be fixed by installing
a SIGTERM handler or by sending SIGINT prior to SIGTERM.
"""

import sys
import os
import signal
import logging
import urllib2
import httplib
import time
import warnings
import socket

from ..behaviours import wsgi_dispatcher
from ..errors import LabourException
from ..http_hit import hit, SUCCESS

# NOTE: makes waitpid() below more readable
NO_OPTIONS = 0

class ServerFailedToStart(LabourException):
    """Raised when we fail to receive a successful page delivery from the
       server during warmup time"""

class Server(object):
    def __init__(self, interface='127.0.0.1', port=8000, do_warmup=True):
        self.interface = interface
        self.port = port
        self.server_pid = None
        self.logger = logging.getLogger('server.ctlr')
        self.do_warmup = do_warmup
    def __str__(self):
        return self.__class__.__name__
    def __repr__(self):
        return '<%s on %s:%s>' % (self.__class__.__name__, self.interface,
                                  self.port,)
    @property
    def address(self):
        return (self.interface, self.port)
    def wait_until_warmup(self, iterations=20, delay=0.5):
        self.logger.info('waiting for server warm-up')
        for iteration in range(iterations):
            # NOTE: give server time to start
            time.sleep(delay)
            result = hit('http://%s:%s' % (self.interface, self.port),
                         timeout=1)
            if result is SUCCESS:
                self.logger.info('server responds OK to requests')
                break
            if type(getattr(result, 'reason', None)) is socket.error:
               continue
            self.logger.warning("caught unexpected %s during warm-up of server" %
                                (result.__class__.__name__,))
        else:
            raise ServerFailedToStart('server failed to start', self.logger)
    def __enter__(self):
        self.logger.info('forking child process to run %s' % (self,))
        self.server_pid = os.fork()
        if self.server_pid == 0:
            try:
                self.logger = logging.getLogger('server.child')
                os.setsid()
                self.start()
            finally:
                # NOTE: we must exit here to make sure we never execute past
                #        the main function of the tested WSGI server
                os._exit(0)
        try:
            if self.do_warmup:
                self.wait_until_warmup()
        except:
            # NOTE: if we failed to warmup for whatever reason, the server's
            #        process was already forked and we must call __exit__()
            #        to kill it
            self.__exit__(*sys.exc_info())
            raise
        return self
    def __exit__(self, error_type, error_value, traceback):
        self.logger.info('sending SIGTERM to server')
        os.kill(self.server_pid, signal.SIGTERM)
        # FIXME: potential deadlock if the server does not die on SIGTERM
        waited_pid, status = os.waitpid(self.server_pid, NO_OPTIONS)
        assert waited_pid == self.server_pid, 'waited for unexpected waitable'
        self.server_pid = None
    def silence_spurious_logging(self, stdout=True, logger_names=()):
        # HACK: cruft to silences servers which spuriously write to stdout
        #       or 'import logging'
        if stdout:
            os.dup2(os.open('/dev/null', os.O_WRONLY), 1)
        for logger_name in logger_names:
            logging.getLogger(logger_name).setLevel(50)

# TODO: remaining servers mentioned in Nicholas' original post: Aspen, Gunicorn, MagnumPy, Tornado, uWSGI and of course, mod_wsgi
