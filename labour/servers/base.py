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

class ServerFailedToStart(LabourException):
    """Raised when we fail to receive a successful page delivery from the
       server during warmup time"""

class Server(object):
    def __init__(self, interface='127.0.0.1', port=8000, do_warmup_wait=True):
        self.interface = interface
        self.port = port
        self.server_pid = None
        self.do_warmup_wait = do_warmup_wait
        self.logger = logging.getLogger('server.ctlr')
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
        warning_fmt = "caught unexpected %s during warm-up of server"
        for iteration in range(iterations):
            # NOTE: give server time to start
            time.sleep(delay)
            try:
                handle = urllib2.urlopen('http://%s:%s' %
                                         (self.interface, self.port))
                handle.read()
                handle.close()
                self.logger.info('server responds OK to requests')
                break
            except urllib2.URLError, error:
                if (hasattr(error, 'reason') and
                    type(error.reason) is socket.error):
                   continue
                self.logger.warning(warning_fmt % (error.__class__.__name__,))
            except httplib.HTTPException, error:
                self.logger.warning(warning_fmt % (error.__class__.__name__,))
        else:
            self.shutdown()
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
        else:
            if self.do_warmup_wait:
                self.wait_until_warmup()
        return self
    def __exit__(self, error_type, error_value, traceback):
        self.shutdown()
    def shutdown(self):
        if self.server_pid is None:
            return
        self.logger.info('sending SIGTERM to server')
        os.kill(self.server_pid, signal.SIGTERM)
        self.server_pid = None
    def silence_spurious_logging(self, stdout=True, logger_names=()):
        # HACK: cruft to silences servers which spuriously write to stdout
        #       or 'import logging'
        if stdout:
            os.dup2(os.open('/dev/null', os.O_WRONLY), 1)
        for logger_name in logger_names:
            logging.getLogger(logger_name).setLevel(50)

# TODO: remaining servers mentioned in Nicholas' original post: Aspen, Gunicorn, MagnumPy, Tornado, uWSGI and of course, mod_wsgi
