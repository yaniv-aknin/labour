#!/usr/bin/env python

# HACK and CRUFT. I know JP Calderone said not to do it, but even
#                 Twisted does it and it sure as heck took me less
#                 time than writing a setup.py

import os

try:
    import labour.executables
except ImportError:
    import sys
    from os.path import join, abspath, isdir, dirname, basename
    from os import path
    possible_project_dir = abspath(path.join(dirname(__file__), '..'))
    if isdir(join(possible_project_dir, 'labour')):
        sys.path.insert(0, possible_project_dir)
    try:
        import labour.executables
    except ImportError, error:
        if '_LABOUR_DEBUG' in os.environ:
            raise
        print("Unable to find required library: " + str(error))
        raise SystemExit(0)

module_name = basename(sys.argv[0])
try:
    module = getattr(labour.executables, module_name)
except AttributeError:
    print("%s is not a labour executable name" % (sys.argv[0]))
else:
    module.main(sys.argv)
