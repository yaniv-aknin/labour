"WSGI Server forking base class and utility functions."

import sys
import os
import signal
import logging
import time
import socket

from ..errors import LabourException
from ..http_hit import hit, SUCCESS
from ..behaviours import wsgi_dispatcher

# NOTE: makes waitpid() below more readable
NO_OPTIONS = 0

class ServerFailedToStart(LabourException):
    """Raised when we fail to receive a successful page delivery from the
       server during warmup time"""

class ServerFailedToExit(Exception):
    """Raised when we signalled the server and it failed to exit, should
       be raised and caught only inside the module."""

class Server(object):
    """This class is a context manager which handles running an
    arbitrary function (meant to be the WSGI Server's start() function
    in a forked process. This class mainly has server-orthogonal process
    forking and shutdown code, as well as the capability to "warmup" a
    server - poll it with dummy requests until it first responds.
    """
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
    def wait_until_warmup(self, iterations=20, delay=0.5):
        self.logger.info('waiting for server warm-up')
        time.sleep(delay)
        wait_while_predicate(
            lambda: not self.is_server_responding(), iterations=iterations,
            delay=delay,
            error=ServerFailedToStart('server failed to start', self.logger),
        )
    def is_server_responding(self):
        result = hit('http://%s:%s' % (self.interface, self.port), timeout=1)
        if result is SUCCESS:
            self.logger.info('server responds OK to requests')
            return True
        if type(getattr(result, 'reason', None)) is not socket.error:
            self.logger.warning("caught unexpected %s during warm-up of server"
                                % (result.__class__.__name__,))
        return False
    def __exit__(self, error_type, error_value, traceback):
        msg = "server at pid %d does not die, giving up" % (self.server_pid,)
        for signal_name in ("SIGINT", "SIGTERM", "SIGKILL"):
            try:
                self.kill_server_and_wait_for_exit(signal_name)
                self.server_pid = None
                return
            except ServerFailedToExit:
                pass
        self.logger.error(msg)
    def kill_server_and_wait_for_exit(self, signal_name):
        self.logger.info('sending %s to server' % (signal_name,))
        os.kill(self.server_pid, getattr(signal, signal_name))
        wait_while_predicate(
            lambda: is_child_still_alive(self.server_pid), iterations=10,
            delay=0.5, error=ServerFailedToExit()
        )
    def silence_spurious_logging(self, stdout=True, logger_names=()):
        # HACK: cruft to silences servers which spuriously write to stdout
        #       or 'import logging'
        devnull = open('/dev/null', 'w')
        if stdout:
            os.dup2(devnull.fileno(), 1)
        for logger_name in logger_names:
            logging.getLogger(logger_name).setLevel(50)
        return devnull

def wait_while_predicate(predicate, iterations, delay, error):
    """General purpose function to wait as long as predicate() is True,
    for up to iterations iterations, waiting delay seconds between each
    predicate evaluation and raising error in case of a timeout."""
    while predicate():
        if iterations == 0:
            raise error
        iterations -= 1
        time.sleep(delay)

def is_child_still_alive(pid):
    return os.waitpid(pid, os.WNOHANG)[0] == 0
