import urllib2
import socket
import httplib

SUCCESS = 'successful response'
CATCH_BY_DEFAULT = (httplib.HTTPException, urllib2.HTTPError,
                    urllib2.URLError, socket.timeout)
def hit(url, timeout=None, catchables=CATCH_BY_DEFAULT):
    try:
        handle = urllib2.urlopen(url, timeout=timeout)
        handle.read()
        handle.close()
        return SUCCESS
    except catchables, error:
        return error
