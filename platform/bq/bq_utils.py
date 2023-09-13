#!/usr/bin/env python
"""A library of functions to handle bq flags consistently."""

import codecs
import http.client
import json
import logging
import os
import pkgutil
import platform
import sys
import textwrap
import time
import traceback
from typing import Dict, Optional

from absl import app
from absl import flags
from google.auth import version as google_auth_version
import googleapiclient
import httplib2
import oauth2client_4_0.client
import requests
import six
import urllib3

import bigquery_client

FLAGS = flags.FLAGS

_GDRIVE_SCOPE = 'https://www.googleapis.com/auth/drive'
_BIGQUERY_SCOPE = 'https://www.googleapis.com/auth/bigquery'
_CLOUD_PLATFORM_SCOPE = 'https://www.googleapis.com/auth/cloud-platform'
_REAUTH_SCOPE = 'https://www.googleapis.com/auth/accounts.reauth'


_BIGQUERY_TOS_MESSAGE = (
    'In order to get started, please visit the Google APIs Console to '
    'create a project and agree to our Terms of Service:\n'
    '\thttps://console.cloud.google.com/\n\n'
    'For detailed sign-up instructions, please see our Getting Started '
    'Guide:\n'
    '\thttps://cloud.google.com/bigquery/docs/quickstarts/'
    'quickstart-command-line\n\n'
    'Once you have completed the sign-up process, please try your command '
    'again.')
_VERSION_FILENAME = 'VERSION'


def _GetVersion():
  """Returns content of VERSION file found in same dir as the cli binary."""
  root = 'bq_utils'
  # pragma pylint: disable=line-too-long
  return six.ensure_str(pkgutil.get_data(root, _VERSION_FILENAME)).strip()


VERSION_NUMBER = _GetVersion()


def GetBigqueryRcFilename():
  """Return the name of the bigqueryrc file to use.

  In order, we look for a flag the user specified, an environment
  variable, and finally the default value for the flag.

  Returns:
    bigqueryrc filename as a string.
  """
  return ((FLAGS['bigqueryrc'].present and FLAGS.bigqueryrc) or
          os.environ.get('BIGQUERYRC') or FLAGS.bigqueryrc)


def GetGcloudConfigFilename() -> str:
  """Returns the best guess for the user's gcloud configuration file."""
  home = os.environ.get('HOME')
  if not home:
    return ''
  try:
    with open(home + '/.config/gcloud/active_config') as active_config_file:
      active_config = active_config_file.read().strip()
      return home + '/.config/gcloud/configurations/config_' + active_config
  except IOError:
    logging.warning('Could not find gcloud config file')
    return ''


def UpdateFlag(flag_values, flag: str, value) -> None:
  # This updates the .value and .present attributes.
  flag_values[flag].parse(value)
  # This updates the .using_default_value attribute in addition.
  setattr(flag_values, flag, getattr(flag_values, flag))


def ProcessGcloudConfig(flag_values) -> None:
  """Processes the user's gcloud config and applies that configuration to BQ."""
  gcloud_file_name = GetGcloudConfigFilename()
  if not gcloud_file_name:
    logging.warning('Not processing gcloud config file since it is not found')
    return
  try:
    auth_config = ProcessConfigSection(
        filename=gcloud_file_name, section_name='auth'
    )
    core_config = ProcessConfigSection(
        filename=gcloud_file_name, section_name='core'
    )
  except IOError:
    logging.warning('Could not load gcloud config data')
    return
  try:
    access_token_file = auth_config['access_token_file']
    universe_domain = core_config['universe_domain']
  except KeyError:
    # This is expected if these attributes aren't in the config file.
    return
  if (
      access_token_file is not None
      and universe_domain is not None
  ):
    logging.info(
        'Using the gcloud configuration to get TPC authorisation from'
        ' access_token_file'
    )
    if (
        not flag_values['oauth_access_token'].using_default_value
        or not flag_values['use_google_auth'].using_default_value
        or not flag_values['api'].using_default_value
    ):
      logging.warning(
          'Users gcloud config file and bigqueryrc file have incompatible'
          ' configurations. Defaulting to the bigqueryrc file'
      )
    try:
      with open(access_token_file) as token_file:
        token = token_file.read().strip()
    except IOError:
      logging.warning(
          'Could not open `access_token_file` file, ignoring gcloud settings'
      )
    else:
      UpdateFlag(flag_values, 'oauth_access_token', token)
      UpdateFlag(flag_values, 'use_google_auth', True)
      UpdateFlag(
          flag_values,
          'api',
          'https://bigquery.' + universe_domain,
      )


def ProcessBigqueryrc():
  """Updates FLAGS with values found in the bigqueryrc file."""
  ProcessBigqueryrcSection(None, FLAGS)


def ProcessConfigSection(
    filename: str, section_name: Optional[str] = None
) -> Dict[str, str]:
  """Read a configuration file section returned as a dictionary.

  Args:
    filename: The filename of the configuration file.
    section_name: if None, read the global flag settings.

  Returns:
    A dictionary of flag names and values from that section of the file.
  """

  # TODO(b/286571605): Replace typing when python 3.5 is unsupported.
  dictionary = {}  # type: Dict[str, str]
  if not os.path.exists(filename):
    return dictionary
  try:
    with open(filename) as rcfile:
      in_section = not section_name
      for line in rcfile:
        if line.lstrip().startswith('[') and line.rstrip().endswith(']'):
          next_section = line.strip()[1:-1]
          in_section = section_name == next_section
          continue
        elif not in_section:
          continue
        elif line.lstrip().startswith('#') or not line.strip():
          continue
        flag, equalsign, value = line.partition('=')
        # if no value given, assume stringified boolean true
        if not equalsign:
          value = 'true'
        flag = flag.strip()
        value = value.strip()
        while flag.startswith('-'):
          flag = flag[1:]
        dictionary[flag] = value
  except IOError:
    pass
  return dictionary


def ProcessBigqueryrcSection(section_name: Optional[str], flag_values) -> None:
  """Read the bigqueryrc file into flag_values for section section_name.

  Args:
    section_name: if None, read the global flag settings.
    flag_values: FLAGS instance.

  Raises:
    UsageError: Unknown flag found.
  """

  bigqueryrc = GetBigqueryRcFilename()
  dictionary = ProcessConfigSection(
      filename=bigqueryrc, section_name=section_name
  )
  for flag, value in dictionary.items():
    # We want flags specified at the command line to override
    # those in the flagfile.
    if flag not in flag_values:
      raise app.UsageError(
          'Unknown flag %s found in bigqueryrc file in section %s' %
          (flag, section_name if section_name else 'global'))
    if not flag_values[flag].present:
      UpdateFlag(flag_values, flag, value)
    else:
      flag_type = flag_values[flag].flag_type()
      if flag_type.startswith('multi'):
        old_value = getattr(flag_values, flag)
        flag_values[flag].parse(value)
        setattr(flag_values, flag, old_value + getattr(flag_values, flag))


def GetPlatformString():
  return':'.join([
      platform.python_implementation(),
      platform.python_version(),
      platform.platform()
  ])


def ProcessError(
    err,
    name='unknown',
    message_prefix='You have encountered a bug in the BigQuery CLI.'):
  """Translate an error message into some printing and a return code."""

  bigquery_client.ConfigurePythonLogger(FLAGS.apilog)
  logger = logging.getLogger(__name__)

  if isinstance(err, SystemExit):
    logger.exception('An error has caused the tool to exit', exc_info=err)
    return err.code  # sys.exit called somewhere, hopefully intentionally.

  response = []
  retcode = 1

  (etype, value, tb) = sys.exc_info()
  trace = ''.join(traceback.format_exception(etype, value, tb))
  # pragma pylint: disable=line-too-long
  contact_us_msg = (
      'Please file a bug report in our '
      'public '
      'issue tracker:\n'
      '  https://issuetracker.google.com/issues/new?component=187149&template=0\n'
      'Please include a brief description of '
      'the steps that led to this issue, as well as '
      'any rows that can be made public from '
      'the following information: \n\n')
  platform_str = GetPlatformString()
  error_details = textwrap.dedent("""\
     ========================================
     == Platform ==
       %s
     == bq version ==
       %s
     == Command line ==
       %s
     == UTC timestamp ==
       %s
     == Error trace ==
     %s
     ========================================
     """) % (
         platform_str,
         six.ensure_str(VERSION_NUMBER),
         [six.ensure_str(item) for item in sys.argv],
         time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
         six.ensure_str(trace))

  codecs.register_error('strict', codecs.replace_errors)
  message = bigquery_client.EncodeForPrinting(err)
  if isinstance(err, (bigquery_client.BigqueryNotFoundError,
                      bigquery_client.BigqueryDuplicateError)):
    response.append('BigQuery error in %s operation: %s' % (name, message))
    retcode = 2
  elif isinstance(err, bigquery_client.BigqueryTermsOfServiceError):
    response.append(str(err) + '\n')
    response.append(_BIGQUERY_TOS_MESSAGE)
  elif isinstance(err, bigquery_client.BigqueryInvalidQueryError):
    response.append('Error in query string: %s' % (message,))
  elif (isinstance(err, bigquery_client.BigqueryError) and
        not isinstance(err, bigquery_client.BigqueryInterfaceError)):
    response.append('BigQuery error in %s operation: %s' % (name, message))
  elif isinstance(err, (app.UsageError, TypeError)):
    response.append(message)
  elif (isinstance(err, SyntaxError) or
        isinstance(err, bigquery_client.BigquerySchemaError)):
    response.append('Invalid input: %s' % (message,))
  elif isinstance(err, flags.Error):
    response.append('Error parsing command: %s' % (message,))
  elif isinstance(err, KeyboardInterrupt):
    response.append('')
  else:  # pylint: disable=broad-except
    # Errors with traceback information are printed here.
    # The traceback module has nicely formatted the error trace
    # for us, so we don't want to undo that via TextWrap.
    if isinstance(err, bigquery_client.BigqueryInterfaceError):
      message_prefix = (
          'Bigquery service returned an invalid reply in %s operation: %s.'
          '\n\n'
          'Please make sure you are using the latest version '
          'of the bq tool and try again. '
          'If this problem persists, you may have encountered a bug in the '
          'bigquery client.' % (name, message))
    elif isinstance(err, oauth2client_4_0.client.Error):
      message_prefix = (
          'Authorization error. This may be a network connection problem, '
          'so please try again. If this problem persists, the credentials '
          'may be corrupt. Try deleting and re-creating your credentials. '
          'You can delete your credentials using '
          '"bq init --delete_credentials".'
          '\n\n'
          'If this problem still occurs, you may have encountered a bug '
          'in the bigquery client.')
    elif (isinstance(err, http.client.HTTPException) or
          isinstance(err, googleapiclient.errors.Error) or
          isinstance(err, httplib2.HttpLib2Error)):
      message_prefix = (
          'Network connection problem encountered, please try again.'
          '\n\n'
          'If this problem persists, you may have encountered a bug in the '
          'bigquery client.')

    message = message_prefix + ' ' + contact_us_msg
    wrap_error_message = True
    if wrap_error_message:
      message = flags.text_wrap(message)
    print(message)
    print(error_details)
    response.append('Unexpected exception in %s operation: %s' %
                    (name, message))

  response_message = '\n'.join(response)
  wrap_error_message = True
  if wrap_error_message:
    response_message = flags.text_wrap(response_message)
  logger.exception(response_message, exc_info=err)
  print(response_message)
  return retcode


def GetInfoString():
  """Gets the info string for the current execution."""
  platform_str = GetPlatformString()
  try:
    httplib2_version = httplib2.__version__
  except AttributeError:
    # Handle an unexpected version being loaded
    # pytype: disable=module-attr
    httplib2_version = httplib2.python3.__version__
    # pytype: enable=module-attr
  try:
    shell_path = os.environ['PATH']
  except KeyError:
    shell_path = None
  try:
    python_path = os.environ['PYTHONPATH']
  except KeyError:
    python_path = None
  return textwrap.dedent(
      """\
      BigQuery CLI [{version}]

      Platform: [{platform_str}] {uname}
      Python Version: [{python_version}]

      Requests Version: [{requests_version}]
      Urllib3 Version: [{urllib3_version}]
      Httplib2: [{httplib2_version}]
      Google Auth Version: [{google_auth_version}]

      System PATH: [{sys_path}]
      Shell PATH: [{shell_path}]
      Python PATH: [{python_path}]

      """.format(
          version=VERSION_NUMBER,
          platform_str=platform_str,
          uname=platform.uname(),
          python_version=sys.version.replace('\n', ' '),
          httplib2_version=httplib2_version,
          google_auth_version=google_auth_version.__version__,
          requests_version=requests.__version__,
          urllib3_version=urllib3.__version__,
          sys_path=os.pathsep.join(sys.path),
          shell_path=shell_path,
          python_path=python_path,
      )
  )


def PrintFormattedJsonObject(obj, default_format='json'):
  """Prints obj in a JSON format according to the "--format" flag.

  Args:
    obj: The object to print.
    default_format: The format to use if the "--format" flag does not specify a
      valid json format: 'json' or 'prettyjson'.
  """
  json_formats = ['json', 'prettyjson']
  if FLAGS.format in json_formats:
    use_format = FLAGS.format
  else:
    use_format = default_format

  if use_format == 'json':
    print(json.dumps(obj, separators=(',', ':')))
  elif use_format == 'prettyjson':
    print(json.dumps(obj, sort_keys=True, indent=2))
  else:
    raise ValueError(
        'Invalid json format for printing: \'%s\', expected one of: %s' %
        (use_format, json_formats))


def GetClientScopeFromFlags():
  """Returns auth scopes based on user supplied flags."""
  client_scope = [_BIGQUERY_SCOPE, _CLOUD_PLATFORM_SCOPE]
  if FLAGS.enable_gdrive:
    client_scope.append(_GDRIVE_SCOPE)
  client_scope.append(_REAUTH_SCOPE)
  return client_scope


def GetClientScopesFor3pi():
  return [_CLOUD_PLATFORM_SCOPE]


def ParseTags(tags: str) -> Dict[str, str]:
  """Parses a list of user-supplied string representing tags.

  Args:
    tags: A comma separated user-supplied string representing tags. It is
      expected to be in the format "key1:value1,key2:value2".

  Returns:
    A dictionary mapping tag keys to tag values.

  Raises:
    UsageError: Incorrect tags or no tags are supplied.
  """
  tags = tags.strip()
  if not tags:
    raise app.UsageError('No tags supplied')
  tags_dict = {}
  for key_value in tags.split(','):
    k, _, v = key_value.partition(':')
    k = k.strip()
    if not k:
      raise app.UsageError('Tag key cannot be None')
    v = v.strip()
    if not v:
      raise app.UsageError('Tag value cannot be None')
    if k in tags_dict:
      raise app.UsageError('Cannot specify tag key "%s" multiple times' % k)
    tags_dict[k] = v
  return tags_dict
