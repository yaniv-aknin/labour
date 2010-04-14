#!/usr/bin/env python

# HACK. I know JP Calderone said not to do it, but even Twisted does
#       it and it sure as heck took me less time than writing a
#       setup.py

import os

try:
    try:
        import labour.executables
    except ImportError:
        import sys
        from os.path import join, abspath, isdir, dirname, basename
        from os import path
        possible_project_dir = abspath(path.join(dirname(__file__), '..'))
        if isdir(join(possible_project_dir, 'labour')):
            sys.path.insert(0, possible_project_dir)
        import labour.executables

    module_name = basename(sys.argv[0])
    module = getattr(labour.executables, module_name)
except ImportError, error:
    if '_LABOUR_DEBUG' in os.environ:
        raise
    print("Unable to find required library: " + str(error))
else:
    module.main(sys.argv)
