import sys, os
import logging

from settings import PIPETTER_LOG_PATH

sys.path.append(os.path.abspath(os.path.pardir))

def setup_logger(name:str,
                 log_path:str,
                 file_handler_level=logging.INFO,
                 stream_handler_level=logging.INFO
                 ):
    # better logging format in console
    class CustomFormatter(logging.Formatter):
        grey = "\x1b[38;20m"
        yellow = "\x1b[33;20m"
        red = "\x1b[31;20m"
        bold_red = "\x1b[31;1m"
        reset = "\x1b[0m"
        format = "%(asctime)s-%(name)s-%(levelname)s-%(message)s(%(filename)s:%(lineno)d)"

        FORMATS = {logging.DEBUG: grey + format + reset,
            logging.INFO: yellow + format + reset,
            logging.WARNING: yellow + format + reset,
            logging.ERROR: red + format + reset,
            logging.CRITICAL: bold_red + format + reset}

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # create file handler which logs even debug messages
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(file_handler_level)

    # create console handler with a higher log level
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(stream_handler_level)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s-%(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(CustomFormatter())
    # add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger

if __name__ == "__main__":
    logger = setup_logger('main', PIPETTER_LOG_PATH)