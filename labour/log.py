import logging

import labour

def setup_logging():
    logging.basicConfig(level=logging.INFO)
    logging.info('labour %s at your service.' % (labour.__version_str__,))
