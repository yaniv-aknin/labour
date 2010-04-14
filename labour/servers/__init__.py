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
