import logging

class LabourException(Exception):
    def __init__(self, msg, logger):
        self.msg = msg
        self.logger = logger
    def log(self):
        self.logger.error(self.msg)

def main_error_handler(main_function):
    def callable(*args, **kwargs):
        try:
            main_function(*args, **kwargs)
        except LabourException, error:
            error.log()
        except KeyboardInterrupt:
            print('\nCtrl-C hit. Aborting, orphaned subprocess might remain.')
    callable.__name__ = main_function.__name__
    callable.__doc__ = main_function.__doc__
    return callable
