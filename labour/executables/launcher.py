#!/usr/bin/env python

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
    print("Unable to find required library: " + str(error))
else:
    module.main(sys.argv)
