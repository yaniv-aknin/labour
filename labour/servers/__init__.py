supported_servers = ("WSGIRef", "Cogen", "Twisted", "Paster", "CherryPy",
                     "FAPWS3", "Gevent", "Tornado", "Eventlet",)
servers = {}

for server_name in supported_servers:
    try:
        # HACK: I'm not sure how to do this without lots of copy and paste
        exec 'from server_%s import %s' % (server_name.lower(), server_name)
        exec 'servers["%s"] = %s' % (server_name, server_name)
    except ImportError:
        pass
