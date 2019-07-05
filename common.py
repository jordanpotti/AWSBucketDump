# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Borrowed from GFYP codebase, work by Kristov Atlas 

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
