"""Shared functions and constants"""
import sys
import logging

LOG_FILENAME = 'awsbucketdump.log'

BOLD = ""
END = ""
if sys.platform != 'win32' and sys.stdout.isatty():
    BOLD = "\033[1m"
    END = "\033[0m"

def pretty_print(string):
    """For *nix systems, augment TTY output. For others, strip such syntax."""
    string = string.replace('$BOLD$', BOLD)
    string = string.replace('$END$', END)
    print(string)

def log(msg, level=logging.INFO):
    """Add a string to the log file."""
    logging.basicConfig(filename=LOG_FILENAME,
                        format='%(asctime)s:%(levelname)s:%(message)s',
                        level=logging.INFO)
    if level == logging.DEBUG:
        logging.debug(msg)
    elif level == logging.INFO:
        logging.info(msg)
    elif level == logging.WARNING:
        logging.warning(msg)
    elif level == logging.ERROR:
        logging.error(msg)
    elif level == logging.CRITICAL:
        logging.critical(msg)
    else:
        raise ValueError(str(level))
