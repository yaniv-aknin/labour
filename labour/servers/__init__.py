"""This package abstracts the task of starting various WSGI Servers
wired to serve our WSGI Application (see the Behaviours module).

The base submodule contains the base class handling the non-server-
specific details of calling a callable in a forked process (a Pythonic
exec(), if you will).

The various server specific submodules (server_wsgiref.py,
server_cogen.py, etc) hold the minimum server-specific code required
to run a particular server.

The sequence supported_servers contans all the server names that this
version of Labour is aware of.

The server_map mapping maps server names to server classes for every
server that seems to be installed on the system during a particular
invocation of Labour (see the ultra hack below which makes it).
"""

supported_servers = ("WSGIRef", "Cogen", "Twisted", "Paster", "CherryPy",
                     "Gevent", "Tornado", "Eventlet",)
server_map = {}

for server_name in supported_servers:
    try:
        # ULTRA HACK: I'm not sure how to do this without repeating myself
        exec 'from server_%s import %s' % (server_name.lower(), server_name)
        exec 'server_map["%s"] = %s' % (server_name, server_name)
    except ImportError:
        pass
