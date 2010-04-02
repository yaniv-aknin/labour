import logging

import labour

def add_argparse_verbosity_options(parser):
    parser.add_argument('-v', '--verbose', action='append_const', dest='verbosity', const=-10)
    parser.add_argument('-q', '--quiet', action='append_const', dest='verbosity', const=10)

def setup_logging(options, level=logging.INFO):
    if options.verbosity is not None:
        level = sum(options.verbosity, level)
    logging.basicConfig(
                        level=level,
                        format='%(asctime)s %(name)-15s %(levelname)-8s %(message)s',
                        datefmt='%Y%m%d-%H%M%S',
                       )
    logging.info('labour %s at your service.' % (labour.__version_str__,))
