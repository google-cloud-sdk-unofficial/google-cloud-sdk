#!/usr/bin/env python
"""Utility functions for BQ CLI logging."""

import datetime
import logging
import os
import sys
from typing import Optional, TextIO, Union

from absl import flags
from absl import logging as absl_logging
from googleapiclient import model

_UNIQUE_SUFFIX: str = ''


def GetUniqueSuffix() -> str:
  global _UNIQUE_SUFFIX
  if not _UNIQUE_SUFFIX:
    _UNIQUE_SUFFIX = datetime.datetime.now().strftime('%z_%Y%m%d_%H%M%S.%f')
  return _UNIQUE_SUFFIX


def SaveStringToLogDirectoryIfTest(
    file_prefix: str, content: Union[str, bytes]
):
  """Saves string content to a file in the log directory."""
  if 'TEST_UNDECLARED_OUTPUTS_DIR' in os.environ:
    if isinstance(content, bytes):
      content = content.decode('utf-8')
    filename = f'{file_prefix}_{GetUniqueSuffix()}.log'
    path = os.path.join(os.environ['TEST_UNDECLARED_OUTPUTS_DIR'], filename)
    with open(path, 'w') as f:
      f.write(content)


def _SetLogFile(logfile: TextIO):
  absl_logging.use_python_logging(quiet=True)
  absl_logging.get_absl_handler().python_handler.stream = logfile


def ConfigurePythonLogger(apilog: Optional[str] = None):
  """Sets up Python logger.

  Applications can configure logging however they want, but this
  captures one pattern of logging which seems useful when dealing with
  a single command line option for determining logging.

  Args:
    apilog: To log to sys.stdout, specify '', '-', '1', 'true', or 'stdout'. To
      log to sys.stderr, specify 'stderr'. To log to a file, specify the file
      path. Specify None to disable logging.
  """
  final_log_message = ''
  if apilog is None:
    try:
      unique_suffix = GetUniqueSuffix()
      apilog = os.path.join(
          os.environ['TEST_UNDECLARED_OUTPUTS_DIR'],
          f'bq_cli{unique_suffix}.log',
      )
      final_log_message = (
          'No logging set and TEST_UNDECLARED_OUTPUTS_DIR is set so we are'
          f' in a test environment and will log to file: {apilog}.'
      )
    except KeyError:
      pass  # Not in a test environment.
  if apilog is None:
    # Effectively turn off logging.
    logging.debug(
        'There is no apilog flag so non-critical logging is disabled.'
    )
    logging.disable(logging.CRITICAL)
  else:
    if apilog in ('', '-', '1', 'true', 'stdout'):
      _SetLogFile(sys.stdout)
    elif apilog == 'stderr':
      _SetLogFile(sys.stderr)
    elif apilog:
      _SetLogFile(open(apilog, 'a'))
    else:
      logging.basicConfig(level=logging.INFO)
    # Turn on apiclient logging of http requests and responses. (Here
    # we handle both the flags interface from apiclient < 1.2 and the
    # module global in apiclient >= 1.2.)
    if hasattr(flags.FLAGS, 'dump_request_response'):
      flags.FLAGS.dump_request_response = True
    else:
      model.dump_request_response = True
  if final_log_message:
    logging.info(final_log_message)


def EncodeForPrinting(o: object) -> str:
  """Safely encode an object as the encoding for sys.stdout."""
  # Not all file objects provide an encoding attribute, so we make sure to
  # handle the case where the attribute is completely absent.
  encoding = getattr(sys.stdout, 'encoding', None) or 'ascii'
  # We want to prevent conflicts in python2 between formatting
  # a str type with a unicode type, e.g. b'abc%s' % (u'[unicode]',)
  # where the byte type will be auto decoded as ascii thus causing
  # an error.
  # Thus we only want to encode the object if it's passed in as a
  # unicode type and the unicode type is not a str type.
  if isinstance(o, type('')) and not isinstance(o, str):
    return o.encode(encoding, 'backslashreplace')
  else:
    return str(o)


def ConfigureLogging(apilog: Optional[str] = None):
  try:
    ConfigurePythonLogger(apilog)
  except IOError as e:
    if e.errno == 2:
      print('Could not configure logging. %s: %s' % (e.strerror, e.filename))
      sys.exit(1)
    raise e
