"""Utility module for 'hitting' an HTTP URL, returning a slightly more
uniform set of results than the usual hodgepodge urllib2.urlopen
returns and raises."""

import urllib2
import socket
import httplib

SUCCESS = 'successful response'
CATCH_BY_DEFAULT = (httplib.HTTPException, urllib2.HTTPError,
                    urllib2.URLError, socket.timeout)
def hit(url, timeout=None, catchables=CATCH_BY_DEFAULT):
    """Hit url within timeout, return the SUCCESS constant or the
    exception raised, if it is listed in the catchables sequence."""
    try:
        handle = urllib2.urlopen(url, timeout=timeout)
        handle.read()
        handle.close()
        return SUCCESS
    except catchables, error:
        return error
