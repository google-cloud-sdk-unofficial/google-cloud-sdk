#!/usr/bin/env python
# Copyright 2012 Google Inc. All Rights Reserved.
"""Bigquery Client library for Python."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import abc
import collections
import datetime
import hashlib
import json
import logging
import os
import random
import re
import string
import sys
import time
from typing import Dict, List, NamedTuple, Optional, Tuple, Union


from absl import flags
import googleapiclient
import httplib2

from utils import bq_api_utils
from utils import bq_error
from utils import bq_id_utils
from utils import bq_processor_utils

collections_abc = collections
if sys.version_info > (3, 8):
  collections_abc = collections.abc

Service = bq_api_utils.Service


# Maps supported connection type names to the corresponding property in the
# connection proto.
CONNECTION_TYPE_TO_PROPERTY_MAP = {
    'CLOUD_SQL': 'cloudSql',
    'AWS': 'aws',
    'Azure': 'azure',
    'SQL_DATA_SOURCE': 'sqlDataSource',
    'CLOUD_SPANNER': 'cloudSpanner',
    'CLOUD_RESOURCE': 'cloudResource',
    'SPARK': 'spark',
}
CONNECTION_PROPERTY_TO_TYPE_MAP = {
    p: t for t, p in CONNECTION_TYPE_TO_PROPERTY_MAP.items()
}
CONNECTION_TYPES = CONNECTION_TYPE_TO_PROPERTY_MAP.keys()


_COLUMNS_TO_INCLUDE_FOR_TRANSFER_RUN = [
    'updateTime', 'schedule', 'runTime', 'scheduleTime', 'params', 'endTime',
    'dataSourceId', 'destinationDatasetId', 'state', 'startTime', 'name'
]

# These columns appear to be empty with scheduling a new transfer run
# so there are listed as excluded from the transfer run output.
_COLUMNS_EXCLUDED_FOR_MAKE_TRANSFER_RUN = ['schedule', 'endTime', 'startTime']


def _PrintFormattedJsonObject(obj, obj_format='json'):
  """Prints obj in a JSON format according to the format argument.

  Args:
    obj: The object to print.
    obj_format: The format to use: 'json' or 'prettyjson'.
  """
  json_formats = ['json', 'prettyjson']

  if obj_format == 'json':
    print(json.dumps(obj, separators=(',', ':')))
  elif obj_format == 'prettyjson':
    print(json.dumps(obj, sort_keys=True, indent=2))
  else:
    raise ValueError(
        'Invalid json format for printing: \'%s\', expected one of: %s' %
        (obj_format, json_formats))


def MaybePrintManualInstructionsForConnection(connection, flag_format=None):
  """Prints follow-up instructions for created or updated connections."""

  if not connection:
    return

  if connection.get('aws') and connection['aws'].get('crossAccountRole'):
    obj = {
        'iamRoleId': connection['aws']['crossAccountRole'].get('iamRoleId'),
        'iamUserId': connection['aws']['crossAccountRole'].get('iamUserId'),
        'externalId': connection['aws']['crossAccountRole'].get('externalId')
    }
    if flag_format in ['prettyjson', 'json']:
      _PrintFormattedJsonObject(obj, obj_format=flag_format)
    else:
      print(('Please add the following identity to your AWS IAM Role \'%s\'\n'
             'IAM user: \'%s\'\n'
             'External Id: \'%s\'\n') %
            (connection['aws']['crossAccountRole'].get('iamRoleId'),
             connection['aws']['crossAccountRole'].get('iamUserId'),
             connection['aws']['crossAccountRole'].get('externalId')))

  if connection.get('aws') and connection['aws'].get('accessRole'):
    obj = {
        'iamRoleId': connection['aws']['accessRole'].get('iamRoleId'),
        'identity': connection['aws']['accessRole'].get('identity')
    }
    if flag_format in ['prettyjson', 'json']:
      _PrintFormattedJsonObject(obj, obj_format=flag_format)
    else:
      print(('Please add the following identity to your AWS IAM Role \'%s\'\n'
             'Identity: \'%s\'\n') %
            (connection['aws']['accessRole'].get('iamRoleId'),
             connection['aws']['accessRole'].get('identity')))

  if connection.get('azure') and connection['azure'].get(
      'federatedApplicationClientId'):
    obj = {
        'federatedApplicationClientId':
            connection['azure'].get('federatedApplicationClientId'),
        'identity':
            connection['azure'].get('identity')
    }
    if flag_format in ['prettyjson', 'json']:
      _PrintFormattedJsonObject(obj, obj_format=flag_format)
    else:
      print((
          'Please add the following identity to your Azure application \'%s\'\n'
          'Identity: \'%s\'\n') %
            (connection['azure'].get('federatedApplicationClientId'),
             connection['azure'].get('identity')))
  elif connection.get('azure'):
    obj = {
        'clientId': connection['azure'].get('clientId'),
        'application': connection['azure'].get('application')
    }
    if flag_format in ['prettyjson', 'json']:
      _PrintFormattedJsonObject(obj, obj_format=flag_format)
    else:
      print(('Please create a Service Principal in your directory '
             'for appId: \'%s\',\n'
             'and perform role assignment to app: \'%s\' to allow BigQuery '
             'to access your Azure data. \n') %
            (connection['azure'].get('clientId'),
             connection['azure'].get('application')))


def _ToFilename(url: str) -> str:
  """Converts a url to a filename."""
  return ''.join([c for c in url if c in string.ascii_lowercase])


def _OverwriteCurrentLine(s: str, previous_token=None) -> int:
  """Print string over the current terminal line, and stay on that line.

  The full width of any previous output (by the token) will be wiped clean.
  If multiple callers call this at the same time, it would be bad.

  Args:
    s: string to print.  May not contain newlines.
    previous_token: token returned from previous call, or None on first call.

  Returns:
    a token to pass into your next call to this function.
  """
  # Tricks in use:
  # carriage return \r brings the printhead back to the start of the line.
  # sys.stdout.write() does not add a newline.

  # Erase any previous, in case new string is shorter.
  if previous_token is not None:
    sys.stderr.write('\r' + (' ' * previous_token))
  # Put new string.
  sys.stderr.write('\r' + s)
  # Display.
  sys.stderr.flush()
  return len(s)


def _FormatLabels(labels: Dict[str, str]) -> str:
  """Format a resource's labels for printing."""
  result_lines = []
  for key, value in labels.items():
    label_str = '%s:%s' % (key, value)
    result_lines.extend([label_str])
  return '\n'.join(result_lines)


def _FormatTableReference(
    table: bq_id_utils.ApiClientHelper.TableReference,
) -> str:
  return '%s:%s.%s' % (
      table['projectId'],
      table['datasetId'],
      table['tableId'],
  )


def _FormatTags(tags: List[Dict[str, str]]) -> str:
  """Format a resource's tags for printing."""
  # When Python 3.6 is supported in client libraries use f-strings
  result_lines = [
      '{}:{}'.format(tag.get('tagKey'), tag.get('tagValue')) for tag in tags
  ]
  return '\n'.join(result_lines)


def _FormatResourceTags(tags: Dict[str, str]) -> str:
  """Format a resource's tags for printing."""
  result_lines = [
      '{}:{}'.format(key, value) for key, value in tags.items()
  ]
  return '\n'.join(result_lines)


def _FormatStandardSqlFields(standard_sql_fields):
  """Returns a string with standard_sql_fields.

  Currently only supports printing primitive field types and repeated fields.
  Args:
    standard_sql_fields: A list of standard sql fields.

  Returns:
    The formatted standard sql fields.
  """
  lines = []
  for field in standard_sql_fields:
    if field['type']['typeKind'] == 'ARRAY':
      field_type = field['type']['arrayElementType']['typeKind']
    else:
      field_type = field['type']['typeKind']
    entry = '|- %s: %s' % (field['name'], field_type.lower())
    if field['type']['typeKind'] == 'ARRAY':
      entry += ' (repeated)'
    lines.extend([entry])
  return '\n'.join(lines)


def _ParseJobIdentifier(
    identifier: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
  """Parses a job identifier string into its components.

  Args:
    identifier: String specifying the job identifier in the format
      "project_id:job_id", "project_id:location.job_id", or "job_id".

  Returns:
    A tuple of three elements: containing project_id, location,
    job_id. If an element is not found, it is represented by
    None. If no elements are found, the tuple contains three None
    values.
  """
  project_id_pattern = r'[\w:\-.]*[\w:\-]+'
  location_pattern = r'[a-zA-Z\-0-9]+'
  job_id_pattern = r'[\w\-]+'

  pattern = re.compile(
      r"""
    ^((?P<project_id>%(PROJECT_ID)s)
    :)?
    ((?P<location>%(LOCATION)s)
    \.)?
    (?P<job_id>%(JOB_ID)s)
    $
  """ % {
      'PROJECT_ID': project_id_pattern,
      'LOCATION': location_pattern,
      'JOB_ID': job_id_pattern
  }, re.X)

  match = re.search(pattern, identifier)
  if match:
    return (match.groupdict().get('project_id', None),
            match.groupdict().get('location',
                                  None), match.groupdict().get('job_id', None))
  return (None, None, None)


def _ParseReservationIdentifier(
    identifier: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
  """Parses the reservation identifier string into its components.

  Args:
    identifier: String specifying the reservation identifier in the format
      "project_id:reservation_id", "project_id:location.reservation_id", or
      "reservation_id".

  Returns:
    A tuple of three elements: containing project_id, location, and
    reservation_id. If an element is not found, it is represented by None.

  Raises:
    bq_error.BigqueryError: if the identifier could not be parsed.
  """

  pattern = re.compile(
      r"""
  ^((?P<project_id>[\w:\-.]*[\w:\-]+):)?
  ((?P<location>[\w\-]+)\.)?
  (?P<reservation_id>[\w\-]*)$
  """, re.X)

  match = re.search(pattern, identifier)
  if not match:
    raise bq_error.BigqueryError(
        'Could not parse reservation identifier: %s' % identifier)

  project_id = match.groupdict().get('project_id', None)
  location = match.groupdict().get('location', None)
  reservation_id = match.groupdict().get('reservation_id', None)
  return (project_id, location, reservation_id)


def ParseReservationPath(
    path: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
  """Parses the reservation path string into its components.

  Args:
    path: String specifying the reservation path in the format
      projects/<project_id>/locations/<location>/reservations/<reservation_id>
      or
      projects/<project_id>/locations/<location>/biReservation

  Returns:
    A tuple of three elements: containing project_id, location and
    reservation_id. If an element is not found, it is represented by None.

  Raises:
    bq_error.BigqueryError: if the path could not be parsed.
  """

  pattern = re.compile(
      r'^projects/(?P<project_id>[\w:\-.]*[\w:\-]+)?' +
      r'/locations/(?P<location>[\w\-]+)?' +
      # Accept a suffix of '/reservations/<reservation ID>' or
      # one of '/biReservation'
      r'/(reservations/(?P<reservation_id>[\w\-/]+)' +
      r'|(?P<bi_id>biReservation)' + r')$',
      re.X)

  match = re.search(pattern, path)
  if not match:
    raise bq_error.BigqueryError(
        'Could not parse reservation path: %s' % path)

  group = lambda key: match.groupdict().get(key, None)
  project_id = group('project_id')
  location = group('location')
  reservation_id = group('reservation_id') or group('bi_id')
  return (project_id, location, reservation_id)


def _ParseCapacityCommitmentIdentifier(
    identifier: str, allow_commas: Optional[bool]
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
  """Parses the capacity commitment identifier string into its components.

  Args:
    identifier: String specifying the capacity commitment identifier in the
      format "project_id:capacity_commitment_id",
      "project_id:location.capacity_commitment_id", or "capacity_commitment_id".
    allow_commas: whether to allow commas in the capacity commitment id.

  Returns:
    A tuple of three elements: containing project_id, location
    and capacity_commitment_id. If an element is not found, it is represented by
    None.

  Raises:
    bq_error.BigqueryError: if the identifier could not be parsed.
  """
  pattern = None
  if allow_commas:
    pattern = re.compile(
        r"""
    ^((?P<project_id>[\w:\-.]*[\w:\-]+):)?
    ((?P<location>[\w\-]+)\.)?
    (?P<capacity_commitment_id>[\w|,-]*)$
    """, re.X)
  else:
    pattern = re.compile(
        r"""
    ^((?P<project_id>[\w:\-.]*[\w:\-]+):)?
    ((?P<location>[\w\-]+)\.)?
    (?P<capacity_commitment_id>[\w|-]*)$
    """, re.X)

  match = re.search(pattern, identifier)
  if not match:
    raise bq_error.BigqueryError(
        'Could not parse capacity commitment identifier: %s' % identifier)

  project_id = match.groupdict().get('project_id', None)
  location = match.groupdict().get('location', None)
  capacity_commitment_id = match.groupdict().get('capacity_commitment_id', None)
  return (project_id, location, capacity_commitment_id)


def ParseCapacityCommitmentPath(
    path: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
  """Parses the capacity commitment path string into its components.

  Args:
    path: String specifying the capacity commitment path in the format
      projects/<project_id>/locations/<location>/capacityCommitments/<capacity_commitment_id>

  Returns:
    A tuple of three elements: containing project_id, location,
    and capacity_commitment_id. If an element is not found, it is represented by
    None.

  Raises:
    bq_error.BigqueryError: if the path could not be parsed.
  """
  pattern = re.compile(
      r"""
  ^projects\/(?P<project_id>[\w:\-.]*[\w:\-]+)?
  \/locations\/(?P<location>[\w\-]+)?
  \/capacityCommitments\/(?P<capacity_commitment_id>[\w|-]+)$
  """, re.X)

  match = re.search(pattern, path)
  if not match:
    raise bq_error.BigqueryError(
        'Could not parse capacity commitment path: %s' % path)

  project_id = match.groupdict().get('project_id', None)
  location = match.groupdict().get('location', None)
  capacity_commitment_id = match.groupdict().get('capacity_commitment_id', None)
  return (project_id, location, capacity_commitment_id)


def _ParseReservationAssignmentIdentifier(
    identifier: str,
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
  """Parses the reservation assignment identifier string into its components.

  Args:
    identifier: String specifying the reservation assignment identifier in the
      format "project_id:reservation_id.assignment_id",
      "project_id:location.reservation_id.assignment_id", or
      "reservation_id.assignment_id".

  Returns:
    A tuple of three elements: containing project_id, location, and
    reservation_assignment_id. If an element is not found, it is represented by
    None.

  Raises:
    bq_error.BigqueryError: if the identifier could not be parsed.
  """

  pattern = re.compile(
      r"""
  ^((?P<project_id>[\w:\-.]*[\w:\-]+):)?
  ((?P<location>[\w\-]+)\.)?
  (?P<reservation_id>[\w\-\/]+)\.
  (?P<reservation_assignment_id>[\w\-_]+)$
  """, re.X)

  match = re.search(pattern, identifier)
  if not match:
    raise bq_error.BigqueryError(
        'Could not parse reservation assignment identifier: %s' % identifier)

  project_id = match.groupdict().get('project_id', None)
  location = match.groupdict().get('location', None)
  reservation_id = match.groupdict().get('reservation_id', None)
  reservation_assignment_id = match.groupdict().get('reservation_assignment_id',
                                                    None)
  return (project_id, location, reservation_id, reservation_assignment_id)


def _ParseReservationAssignmentPath(
    path: str,
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
  """Parses the reservation assignment path string into its components.

  Args:
    path: String specifying the reservation assignment path in the format
      projects/<project_id>/locations/<location>/
      reservations/<reservation_id>/assignments/<assignment_id> The
      reservation_id must be that of a top level reservation.

  Returns:
    A tuple of three elements: containing project_id, location and
    reservation_assignment_id. If an element is not found, it is represented by
    None.

  Raises:
    bq_error.BigqueryError: if the path could not be parsed.
  """

  pattern = re.compile(
      r"""
  ^projects\/(?P<project_id>[\w:\-.]*[\w:\-]+)?
  \/locations\/(?P<location>[\w\-]+)?
  \/reservations\/(?P<reservation_id>[\w\-]+)
  \/assignments\/(?P<reservation_assignment_id>[\w\-_]+)$
  """, re.X)

  match = re.search(pattern, path)
  if not match:
    raise bq_error.BigqueryError(
        'Could not parse reservation assignment path: %s' % path)

  project_id = match.groupdict().get('project_id', None)
  location = match.groupdict().get('location', None)
  reservation_id = match.groupdict().get('reservation_id', None)
  reservation_assignment_id = match.groupdict().get('reservation_assignment_id',
                                                    None)
  return (project_id, location, reservation_id, reservation_assignment_id)


def _ParseConnectionIdentifier(
    identifier: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
  """Parses the connection identifier string into its components.

  Args:
    identifier: String specifying the connection identifier in the format
      "connection_id", "location.connection_id",
      "project_id.location.connection_id"

  Returns:
    A tuple of four elements: containing project_id, location, connection_id
    If an element is not found, it is represented by None.

  Raises:
    bq_error.BigqueryError: if the identifier could not be parsed.
  """

  if not identifier:
    raise bq_error.BigqueryError('Empty connection identifier')

  tokens = identifier.split('.')
  num_tokens = len(tokens)
  if num_tokens > 4:
    raise bq_error.BigqueryError(
        'Could not parse connection identifier: %s' % identifier)
  connection_id = tokens[num_tokens - 1]
  location = tokens[num_tokens - 2] if num_tokens > 1 else None
  project_id = '.'.join(tokens[:num_tokens - 2]) if num_tokens > 2 else None

  return (project_id, location, connection_id)


def _ParseConnectionPath(
    path: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
  """Parses the connection path string into its components.

  Args:
    path: String specifying the connection path in the format
      projects/<project_id>/locations/<location>/connections/<connection_id>

  Returns:
    A tuple of three elements: containing project_id, location and
    connection_id. If an element is not found, it is represented by None.

  Raises:
    bq_error.BigqueryError: if the path could not be parsed.
  """

  pattern = re.compile(
      r"""
  ^projects\/(?P<project_id>[\w:\-.]*[\w:\-]+)?
  \/locations\/(?P<location>[\w\-]+)?
  \/connections\/(?P<connection_id>[\w\-\/]+)$
  """, re.X)

  match = re.search(pattern, path)
  if not match:
    raise bq_error.BigqueryError(
        'Could not parse connection path: %s' % path)

  project_id = match.groupdict().get('project_id', None)
  location = match.groupdict().get('location', None)
  connection_id = match.groupdict().get('connection_id', None)
  return (project_id, location, connection_id)


def ReadTableConstrants(table_constraints: str):
  """Create table constraints json object from string or a file name.

  Args:
    table_constraints: Either a json string that presents a table_constraints
      proto or name of a file that contains the json string.

  Returns:
    The table_constraints (as a json object).

  Raises:
    bq_error.BigqueryTableConstraintsError: If load the table constraints
      from the string or file failed.
  """
  if not table_constraints:
    raise bq_error.BigqueryTableConstraintsError(
        'table_constraints cannot be empty')
  if os.path.exists(table_constraints):
    with open(table_constraints) as f:
      try:
        loaded_json = json.load(f)
      except ValueError as e:
        raise bq_error.BigqueryTableConstraintsError(
            'Error decoding JSON table constraints from file %s.'
            % (table_constraints,)
        ) from e
    return loaded_json
  if re.search(r'^[./~\\]', table_constraints) is not None:
    # The table_constraints looks like a file name but the file does not
    # exist.
    raise bq_error.BigqueryTableConstraintsError(
        'Error reading table constraints: "%s" looks like a filename, '
        'but was not found.' % (table_constraints,)
    )
  try:
    loaded_json = json.loads(table_constraints)
  except ValueError as e:
    raise bq_error.BigqueryTableConstraintsError(
        'Error decoding JSON table constraints from string %s.'
        % (table_constraints,)
    ) from e
  return loaded_json


def RaiseErrorFromHttpError(e):
  """Raises a BigQueryError given an HttpError."""
  if e.resp.get('content-type', '').startswith('application/json'):
    content = json.loads(e.content.decode('utf-8'))
    RaiseError(content)
  else:
    # If the HttpError is not a json object, it is a communication error.
    error_details = ''
    if flags.FLAGS.use_regional_endpoints:
      error_details = ' The specified regional endpoint may not be supported.'
    raise bq_error.BigqueryCommunicationError(
        'Could not connect with BigQuery server.%s\n'
        'Http response status: %s\n'
        'Http response content:\n%s'
        % (error_details, e.resp.get('status', '(unexpected)'), e.content)
    )


def RaiseErrorFromNonHttpError(e):
  """Raises a BigQueryError given a non-HttpError."""
  raise bq_error.BigqueryCommunicationError(
      'Could not connect with BigQuery server due to: %r' % (e,))


class JobIdGenerator(abc.ABC):
  """Base class for job id generators."""

  def __init__(self):
    pass

  @abc.abstractmethod
  def Generate(self, job_configuration):
    """Generates a job_id to use for job_configuration."""


class JobIdGeneratorNone(JobIdGenerator):
  """Job id generator that returns None, letting the server pick the job id."""

  def Generate(self, job_configuration):
    return None


class JobIdGeneratorRandom(JobIdGenerator):
  """Generates random job id_fallbacks."""

  def Generate(self, job_configuration):
    return 'bqjob_r%08x_%016x' % (random.SystemRandom().randint(
        0, sys.maxsize), int(time.time() * 1000))


class JobIdGeneratorFingerprint(JobIdGenerator):
  """Generates job ids that uniquely match the job config."""

  def _HashableRepr(self, obj):
    if isinstance(obj, bytes):
      return obj
    return str(obj).encode('utf-8')

  def _Hash(self, config, sha1):
    """Computes the sha1 hash of a dict."""
    keys = list(config.keys())
    # Python dict enumeration ordering is random. Sort the keys
    # so that we will visit them in a stable order.
    keys.sort()
    for key in keys:
      sha1.update(self._HashableRepr(key))
      v = config[key]
      if isinstance(v, dict):
        logging.info('Hashing: %s...', key)
        self._Hash(v, sha1)
      elif isinstance(v, list):
        logging.info('Hashing: %s ...', key)
        for inner_v in v:
          self._Hash(inner_v, sha1)
      else:
        logging.info('Hashing: %s:%s', key, v)
        sha1.update(self._HashableRepr(v))

  def Generate(self, job_configuration):
    s1 = hashlib.sha1()
    self._Hash(job_configuration, s1)
    job_id = 'bqjob_c%s' % (s1.hexdigest(),)
    logging.info('Fingerprinting: %s:\n%s', job_configuration, job_id)
    return job_id


class JobIdGeneratorIncrementing(JobIdGenerator):
  """Generates job ids that increment each time we're asked."""

  def __init__(self, inner):
    super().__init__()
    self._inner = inner
    self._retry = 0

  def Generate(self, job_configuration):
    self._retry += 1
    return '%s_%d' % (self._inner.Generate(job_configuration), self._retry)


def FormatTime(secs):
  return time.strftime('%d %b %H:%M:%S', time.localtime(secs))


def FormatTimeFromProtoTimestampJsonString(json_string):
  """Converts google.protobuf.Timestamp formatted string to BQ format."""
  parsed_datetime = datetime.datetime.strptime(
      json_string, '%Y-%m-%dT%H:%M:%S.%fZ'
  )
  seconds = (parsed_datetime - datetime.datetime(1970, 1, 1)).total_seconds()
  return FormatTime(seconds)


def FormatAcl(acl):
  """Format a server-returned ACL for printing."""
  acl_entries = collections.defaultdict(list)
  for entry in acl:
    entry = entry.copy()
    view = entry.pop('view', None)
    dataset = entry.pop('dataset', None)
    routine = entry.pop('routine', None)
    if view:
      acl_entries['VIEW'].append(
          '%s:%s.%s' %
          (view.get('projectId'), view.get('datasetId'), view.get('tableId')))
    elif dataset:
      dataset_reference = dataset.get('dataset')
      for target in dataset.get('targetTypes'):
        acl_entries['All ' + target + ' in DATASET'].append(
            '%s:%s'
            % (
                dataset_reference.get('projectId'),
                dataset_reference.get('datasetId'),
            )
        )
    elif routine:
      acl_entries['ROUTINE'].append(
          '%s:%s.%s' % (routine.get('projectId'), routine.get('datasetId'),
                        routine.get('routineId')))
    else:
      role = entry.pop('role', None)
      if not role or len(list(entry.values())) != 1:
        raise bq_error.BigqueryInterfaceError(
            'Invalid ACL returned by server: %s' % acl, {}, [])
      acl_entries[role].extend(entry.values())
  # Show a couple things first.
  original_roles = [('OWNER', 'Owners'), ('WRITER', 'Writers'),
                    ('READER', 'Readers'), ('VIEW', 'Authorized Views')]
  result_lines = []
  for role, name in original_roles:
    members = acl_entries.pop(role, None)
    if members:
      result_lines.append('%s:' % name)
      result_lines.append(',\n'.join('  %s' % m for m in sorted(members)))
  # Show everything else.
  for role, members in sorted(acl_entries.items()):
    result_lines.append('%s:' % role)
    result_lines.append(',\n'.join('  %s' % m for m in sorted(members)))
  return '\n'.join(result_lines)


def FormatSchema(schema):
  """Format a schema for printing."""

  def PrintFields(fields, indent=0):
    """Print all fields in a schema, recurring as necessary."""
    lines = []
    for field in fields:
      prefix = '|  ' * indent
      junction = '|' if field.get('type', 'STRING') != 'RECORD' else '+'
      entry = '%s- %s: %s' % (junction, field['name'],
                              field.get('type', 'STRING').lower())
      # Print type parameters.
      if 'maxLength' in field:
        entry += '(%s)' % (field['maxLength'])
      elif 'precision' in field:
        if 'scale' in field:
          entry += '(%s, %s)' % (field['precision'], field['scale'])
        else:
          entry += '(%s)' % (field['precision'])
        if 'roundingMode' in field:
          entry += ' options(rounding_mode="%s")' % (field['roundingMode'])
      # Print type mode.
      if field.get('mode', 'NULLABLE') != 'NULLABLE':
        entry += ' (%s)' % (field['mode'].lower(),)
      lines.append(prefix + entry)
      if 'fields' in field:
        lines.extend(PrintFields(field['fields'], indent + 1))
    return lines

  return '\n'.join(PrintFields(schema.get('fields', [])))


def NormalizeWait(wait):
  try:
    return int(wait)
  except ValueError:
    raise ValueError('Invalid value for wait: %s' % (wait,))


def ValidatePrintFormat(print_format: str) -> None:
  if print_format not in [
      'show',
      'list',
      'view',
      'materialized_view',
      'make',
      'table_replica',
  ]:
    raise ValueError('Unknown format: %s' % (print_format,))


def _ParseDatasetIdentifier(identifier: str) -> Tuple[str, str]:
  # We need to parse plx datasets separately.
  if identifier.startswith('plx.google:'):
    return 'plx.google', identifier[len('plx.google:'):]
  else:
    project_id, _, dataset_id = identifier.rpartition(':')
    return project_id, dataset_id


def _ShiftInformationSchema(dataset_id: str, table_id: str) -> Tuple[str, str]:
  """Moves "INFORMATION_SCHEMA" to table_id for dataset qualified tables."""
  if not dataset_id or not table_id:
    return dataset_id, table_id

  dataset_parts = dataset_id.split('.')
  if dataset_parts[-1] != 'INFORMATION_SCHEMA' or table_id in (
      'SCHEMATA',
      'SCHEMATA_OPTIONS'):
    # We don't shift unless INFORMATION_SCHEMA is present and table_id is for
    # a dataset qualified table.
    return dataset_id, table_id

  return '.'.join(dataset_parts[:-1]), 'INFORMATION_SCHEMA.' + table_id


def _ParseIdentifier(identifier: str) -> Tuple[str, str, str]:
  """Parses identifier into a tuple of (possibly empty) identifiers.

  This will parse the identifier into a tuple of the form
  (project_id, dataset_id, table_id) without doing any validation on
  the resulting names; missing names are returned as ''. The
  interpretation of these identifiers depends on the context of the
  caller. For example, if you know the identifier must be a job_id,
  then you can assume dataset_id is the job_id.

  Args:
    identifier: string, identifier to parse

  Returns:
    project_id, dataset_id, table_id: (string, string, string)
  """
  # We need to handle the case of a lone project identifier of the
  # form domain.com:proj separately.
  if re.search(r'^\w[\w.]*\.[\w.]+:\w[\w\d_-]*:?$', identifier):
    return identifier, '', ''
  project_id, _, dataset_and_table_id = identifier.rpartition(':')

  if '.' in dataset_and_table_id:
    dataset_id, _, table_id = dataset_and_table_id.rpartition('.')
  elif project_id:
    # Identifier was a project : <something without dots>.
    # We must have a dataset id because there was a project
    dataset_id = dataset_and_table_id
    table_id = ''
  else:
    # Identifier was just a bare id with no dots or colons.
    # Return this as a table_id.
    dataset_id = ''
    table_id = dataset_and_table_id

  dataset_id, table_id = _ShiftInformationSchema(
      dataset_id, table_id)

  return project_id, dataset_id, table_id


def GetProjectReference(
    id_fallbacks: NamedTuple(
        'IDS',
        [
            ('project_id', Optional[str]),
        ],
    ),
    identifier: str = '',
) -> bq_id_utils.ApiClientHelper.ProjectReference:
  """Determine a project reference from an identifier or fallback."""
  project_id, dataset_id, table_id = _ParseIdentifier(
      identifier)
  try:
    # ParseIdentifier('foo') is just a table_id, but we want to read
    # it as a project_id.
    project_id = project_id or table_id or id_fallbacks.project_id
    if not dataset_id and project_id:
      return bq_id_utils.ApiClientHelper.ProjectReference.Create(
          projectId=project_id
      )
  except ValueError:
    pass
  if project_id == '':
    raise bq_error.BigqueryClientError('Please provide a project ID.')
  else:
    raise bq_error.BigqueryClientError(
        'Cannot determine project described by %s' % (identifier,))


def GetDatasetReference(
    id_fallbacks: NamedTuple(
        'IDS',
        [
            ('project_id', Optional[str]),
            ('dataset_id', Optional[str]),
        ],
    ),
    identifier: str = '',
) -> bq_id_utils.ApiClientHelper.DatasetReference:
  """Determine a DatasetReference from an identifier or fallback."""
  identifier = id_fallbacks.dataset_id if not identifier else identifier
  project_id, dataset_id, table_id = _ParseIdentifier(
      identifier)
  if table_id and not project_id and not dataset_id:
    # identifier is 'foo'
    project_id = id_fallbacks.project_id
    dataset_id = table_id
  elif project_id and dataset_id and table_id:
    # Identifier was foo::bar.baz.qux.
    dataset_id = dataset_id + '.' + table_id
  elif project_id and dataset_id and not table_id:
    # identifier is 'foo:bar'
    pass
  else:
    raise bq_error.BigqueryError(
        'Cannot determine dataset described by %s' % (identifier,))

  try:
    return bq_id_utils.ApiClientHelper.DatasetReference.Create(
        projectId=project_id, datasetId=dataset_id)
  except ValueError as e:
    raise bq_error.BigqueryError(
        'Cannot determine dataset described by %s' % (identifier,)) from e


def GetTableReference(
    id_fallbacks: NamedTuple(
        'IDS',
        [
            ('project_id', Optional[str]),
            ('dataset_id', Optional[str]),
        ],
    ),
    identifier: str = '',
    default_dataset_id: str = '',
) -> bq_id_utils.ApiClientHelper.TableReference:
  """Determine a TableReference from an identifier and fallbacks."""
  project_id, dataset_id, table_id = _ParseIdentifier(
      identifier)
  if not dataset_id:
    project_id, dataset_id = _ParseDatasetIdentifier(id_fallbacks.dataset_id)
  if default_dataset_id and not dataset_id:
    dataset_id = default_dataset_id
  try:
    return bq_id_utils.ApiClientHelper.TableReference.Create(
        projectId=project_id or id_fallbacks.project_id,
        datasetId=dataset_id,
        tableId=table_id,
    )
  except ValueError as e:
    raise bq_error.BigqueryError(
        'Cannot determine table described by %s' % (identifier,)) from e


def GetModelReference(
    id_fallbacks: NamedTuple(
        'IDS',
        [
            ('project_id', Optional[str]),
            ('dataset_id', Optional[str]),
        ],
    ),
    identifier: str = '',
) -> bq_id_utils.ApiClientHelper.ModelReference:
  """Returns a ModelReference from an identifier."""
  project_id, dataset_id, table_id = _ParseIdentifier(
      identifier)
  if not dataset_id:
    project_id, dataset_id = _ParseDatasetIdentifier(id_fallbacks.dataset_id)
  try:
    return bq_id_utils.ApiClientHelper.ModelReference.Create(
        projectId=project_id or id_fallbacks.project_id,
        datasetId=dataset_id,
        modelId=table_id)
  except ValueError as e:
    raise bq_error.BigqueryError(
        'Cannot determine model described by %s' % identifier) from e


def GetRoutineReference(
    id_fallbacks: NamedTuple(
        'IDS',
        [
            ('project_id', Optional[str]),
            ('dataset_id', Optional[str]),
        ],
    ),
    identifier: str = '',
) -> bq_id_utils.ApiClientHelper.RoutineReference:
  """Returns a RoutineReference from an identifier."""
  project_id, dataset_id, table_id = _ParseIdentifier(
      identifier)
  if not dataset_id:
    project_id, dataset_id = _ParseDatasetIdentifier(id_fallbacks.dataset_id)
  try:
    return bq_id_utils.ApiClientHelper.RoutineReference.Create(
        projectId=project_id or id_fallbacks.project_id,
        datasetId=dataset_id,
        routineId=table_id)
  except ValueError as e:
    raise bq_error.BigqueryError(
        'Cannot determine routine described by %s' % identifier) from e


def GetQueryDefaultDataset(identifier: str) -> Dict[str, str]:
  parsed_project_id, parsed_dataset_id = _ParseDatasetIdentifier(
      identifier)
  result = dict(datasetId=parsed_dataset_id)
  if parsed_project_id:
    result['projectId'] = parsed_project_id
  return result


def GetReference(
    id_fallbacks: NamedTuple(
        'IDS',
        [
            ('project_id', Optional[str]),
            ('dataset_id', Optional[str]),
        ],
    ),
    identifier: str = '',
) -> Union[
    bq_id_utils.ApiClientHelper.TableReference,
    bq_id_utils.ApiClientHelper.DatasetReference,
    bq_id_utils.ApiClientHelper.ProjectReference,
]:
  """Try to deduce a project/dataset/table reference from a string.

  If the identifier is not compound, treat it as the most specific
  identifier we don't have as a flag, or as the table_id. If it is
  compound, fill in any unspecified part.

  Args:
    id_fallbacks: The IDs cached on BigqueryClient.
    identifier: string, Identifier to create a reference for.

  Returns:
    A valid ProjectReference, DatasetReference, or TableReference.

  Raises:
    bq_error.BigqueryError: if no valid reference can be determined.
  """
  try:
    return GetTableReference(id_fallbacks, identifier)
  except bq_error.BigqueryError:
    pass
  try:
    return GetDatasetReference(id_fallbacks, identifier)
  except bq_error.BigqueryError:
    pass
  try:
    return GetProjectReference(id_fallbacks, identifier)
  except bq_error.BigqueryError:
    pass
  raise bq_error.BigqueryError(
      'Cannot determine reference for "%s"' % (identifier,))


def GetJobReference(
    id_fallbacks: NamedTuple(
        'IDS',
        [
            ('project_id', Optional[str]),
        ],
    ),
    identifier: str = '',
    default_location: Optional[str] = None,
) -> bq_id_utils.ApiClientHelper.JobReference:
  """Determine a JobReference from an identifier, location, and fallbacks."""
  project_id, location, job_id = _ParseJobIdentifier(identifier)
  if not project_id:
    project_id = id_fallbacks.project_id
  if not location:
    location = default_location
  if job_id:
    try:
      return bq_id_utils.ApiClientHelper.JobReference.Create(
          projectId=project_id, jobId=job_id, location=location)
    except ValueError:
      pass
  raise bq_error.BigqueryError(
      'Cannot determine job described by %s' % (identifier,))


def GetReservationReference(
    id_fallbacks: NamedTuple(
        'IDS',
        [
            ('project_id', Optional[str]),
            ('api_version', Optional[str]),
        ],
    ),
    identifier: Optional[str] = None,
    default_location: Optional[str] = None,
    default_reservation_id: Optional[str] = None,
    check_reservation_project: bool = True,
) -> bq_id_utils.ApiClientHelper.ReservationReference:
  """Determine a ReservationReference from an identifier and location."""
  project_id, location, reservation_id = _ParseReservationIdentifier(
      identifier=identifier)
  # For MoveAssignment rpc, reservation reference project can be different
  # from the project_id_fallback. We'll skip this check in this case.
  if (check_reservation_project and project_id and id_fallbacks.project_id and
      project_id != id_fallbacks.project_id):
    raise bq_error.BigqueryError(
        "Specified project '%s' should be the same as the project of the "
        "reservation '%s'." % (id_fallbacks.project_id, project_id))
  project_id = project_id or id_fallbacks.project_id
  if not project_id:
    raise bq_error.BigqueryError('Project id not specified.')
  location = location or default_location
  if not location:
    raise bq_error.BigqueryError('Location not specified.')
  if default_location and location.lower() != default_location.lower():
    raise bq_error.BigqueryError(
        "Specified location '%s' should be the same as the location of the "
        "reservation '%s'." % (default_location, location))
  reservation_id = reservation_id or default_reservation_id
  if not reservation_id:
    raise bq_error.BigqueryError('Reservation name not specified.')
  elif (id_fallbacks.api_version == 'v1beta1'
        ):
    return bq_id_utils.ApiClientHelper.BetaReservationReference(
        projectId=project_id, location=location, reservationId=reservation_id)
  else:
    return bq_id_utils.ApiClientHelper.ReservationReference(
        projectId=project_id, location=location, reservationId=reservation_id)


def GetBiReservationReference(
    id_fallbacks: NamedTuple(
        'IDS',
        [
            ('project_id', Optional[str]),
        ],
    ),
    default_location: Optional[str] = None,
) -> bq_id_utils.ApiClientHelper.BiReservationReference:
  """Determine a ReservationReference from an identifier and location."""
  project_id = id_fallbacks.project_id
  if not project_id:
    raise bq_error.BigqueryError('Project id not specified.')
  location = default_location
  if not location:
    raise bq_error.BigqueryError('Location not specified.')
  return bq_id_utils.ApiClientHelper.BiReservationReference.Create(
      projectId=project_id, location=location)


def GetCapacityCommitmentReference(
    id_fallbacks: NamedTuple(
        'IDS',
        [
            ('project_id', Optional[str]),
        ],
    ),
    identifier: Optional[str] = None,
    path: Optional[str] = None,
    default_location: Optional[str] = None,
    default_capacity_commitment_id: Optional[str] = None,
    allow_commas: Optional[bool] = None,
) -> bq_id_utils.ApiClientHelper.CapacityCommitmentReference:
  """Determine a CapacityCommitmentReference from an identifier and location."""
  if identifier is not None:
    project_id, location, capacity_commitment_id = (
        _ParseCapacityCommitmentIdentifier(identifier, allow_commas)
    )
  elif path is not None:
    project_id, location, capacity_commitment_id = ParseCapacityCommitmentPath(
        path)
  else:
    raise bq_error.BigqueryError(
        'Either identifier or path must be specified.')
  project_id = project_id or id_fallbacks.project_id
  if not project_id:
    raise bq_error.BigqueryError('Project id not specified.')
  location = location or default_location
  if not location:
    raise bq_error.BigqueryError('Location not specified.')
  capacity_commitment_id = (
      capacity_commitment_id or default_capacity_commitment_id
  )
  if not capacity_commitment_id:
    raise bq_error.BigqueryError(
        'Capacity commitment id not specified.')

  return bq_id_utils.ApiClientHelper.CapacityCommitmentReference.Create(
      projectId=project_id,
      location=location,
      capacityCommitmentId=capacity_commitment_id)


def GetReservationAssignmentReference(
    id_fallbacks: NamedTuple(
        'IDS',
        [
            ('project_id', Optional[str]),
            ('api_version', Optional[str]),
        ],
    ),
    identifier: Optional[str] = None,
    path: Optional[str] = None,
    default_location: Optional[str] = None,
    default_reservation_id: Optional[str] = None,
    default_reservation_assignment_id: Optional[str] = None,
) -> bq_id_utils.ApiClientHelper.ReservationAssignmentReference:
  """Determine a ReservationAssignmentReference from inputs."""
  if identifier is not None:
    (project_id, location, reservation_id, reservation_assignment_id
    ) = _ParseReservationAssignmentIdentifier(identifier)
  elif path is not None:
    (project_id, location, reservation_id, reservation_assignment_id) = (
        _ParseReservationAssignmentPath(path)
    )
  else:
    raise bq_error.BigqueryError(
        'Either identifier or path must be specified.')
  project_id = project_id or id_fallbacks.project_id
  if not project_id:
    raise bq_error.BigqueryError('Project id not specified.')
  location = location or default_location
  if not location:
    raise bq_error.BigqueryError('Location not specified.')
  reservation_id = reservation_id or default_reservation_id
  reservation_assignment_id = (
      reservation_assignment_id or default_reservation_assignment_id
  )
  if (id_fallbacks.api_version == 'v1beta1'
      ):
    return (
        bq_id_utils.ApiClientHelper.BetaReservationAssignmentReference.Create(
            projectId=project_id,
            location=location,
            reservationId=reservation_id,
            reservationAssignmentId=reservation_assignment_id,
        )
    )
  else:
    return bq_id_utils.ApiClientHelper.ReservationAssignmentReference.Create(
        projectId=project_id,
        location=location,
        reservationId=reservation_id,
        reservationAssignmentId=reservation_assignment_id)


def GetConnectionReference(
    id_fallbacks: NamedTuple(
        'IDS',
        [
            ('project_id', Optional[str]),
            ('api_version', Optional[str]),
        ],
    ),
    identifier: Optional[str] = None,
    path: Optional[str] = None,
    default_location: Optional[str] = None,
    default_connection_id: Optional[str] = None,
) -> bq_id_utils.ApiClientHelper.ConnectionReference:
  """Determine a ConnectionReference from an identifier and location."""
  if identifier is not None:
    (project_id, location, connection_id) = _ParseConnectionIdentifier(
        identifier
    )
  elif path is not None:
    (project_id, location, connection_id) = _ParseConnectionPath(path)
  project_id = project_id or id_fallbacks.project_id
  if not project_id:
    raise bq_error.BigqueryError('Project id not specified.')
  location = location or default_location
  if not location:
    raise bq_error.BigqueryError('Location not specified.')
  connection_id = connection_id or default_connection_id
  if not connection_id:
    raise bq_error.BigqueryError('Connection name not specified.')
  return bq_id_utils.ApiClientHelper.ConnectionReference.Create(
      projectId=project_id, location=location, connectionId=connection_id)


def ConfigureFormatter(
    formatter, reference_type, print_format='list', object_info=None
):
  """Configure a formatter for a given reference type.

  If print_format is 'show', configures the formatter with several
  additional fields (useful for printing a single record).

  Arguments:
    formatter: TableFormatter object to configure.
    reference_type: Type of object this formatter will be used with.
    print_format: Either 'show' or 'list' to control what fields are included.

  Raises:
    ValueError: If reference_type or format is unknown.
  """
  ValidatePrintFormat(print_format)
  if reference_type == bq_id_utils.ApiClientHelper.JobReference:
    if print_format == 'list':
      formatter.AddColumns(('jobId',))
    formatter.AddColumns((
        'Job Type',
        'State',
        'Start Time',
        'Duration',
    ))
    if print_format == 'show':
      formatter.AddColumns(('User Email',))
      formatter.AddColumns(('Bytes Processed',))
      formatter.AddColumns(('Bytes Billed',))
      formatter.AddColumns(('Billing Tier',))
      formatter.AddColumns(('Labels',))
  elif reference_type == bq_id_utils.ApiClientHelper.ProjectReference:
    if print_format == 'list':
      formatter.AddColumns(('projectId',))
    formatter.AddColumns(('friendlyName',))
  elif reference_type == bq_id_utils.ApiClientHelper.DatasetReference:
    if print_format == 'list':
      formatter.AddColumns(('datasetId',))
    if print_format == 'show':
      formatter.AddColumns((
          'Last modified',
          'ACLs',
      ))
      formatter.AddColumns(('Labels',))
      add_tags = 'tags' in object_info
      if add_tags:
        formatter.AddColumns(('Tags',))
      if 'defaultEncryptionConfiguration' in object_info:
        formatter.AddColumns(('kmsKeyName',))
      if 'type' in object_info:
        formatter.AddColumns(('Type',))
      if 'linkedDatasetSource' in object_info:
        formatter.AddColumns(('Source dataset',))
      if 'maxTimeTravelHours' in object_info:
        formatter.AddColumns(('Max time travel (Hours)',))
  elif reference_type == bq_id_utils.ApiClientHelper.TransferConfigReference:
    if print_format == 'list':
      formatter.AddColumns(('name',))
      formatter.AddColumns(('displayName',))
      formatter.AddColumns(('dataSourceId',))
      formatter.AddColumns(('state',))
    if print_format == 'show':
      for key in object_info.keys():
        if key != 'name':
          formatter.AddColumns((key,))
  elif reference_type == bq_id_utils.ApiClientHelper.TransferRunReference:
    if print_format == 'show':
      for column in _COLUMNS_TO_INCLUDE_FOR_TRANSFER_RUN:
        if column != 'name':
          formatter.AddColumns((column,))
    elif print_format == 'list':
      for column in _COLUMNS_TO_INCLUDE_FOR_TRANSFER_RUN:
        formatter.AddColumns((column,))
    elif print_format == 'make':
      for column in _COLUMNS_TO_INCLUDE_FOR_TRANSFER_RUN:
        if column not in (_COLUMNS_EXCLUDED_FOR_MAKE_TRANSFER_RUN):
          formatter.AddColumns((column,))
  elif reference_type == bq_id_utils.ApiClientHelper.TransferLogReference:
    formatter.AddColumns(('messageText',))
    formatter.AddColumns(('messageTime',))
    formatter.AddColumns(('severity',))
  elif reference_type == bq_id_utils.ApiClientHelper.NextPageTokenReference:
    formatter.AddColumns(('nextPageToken',))
  elif reference_type == bq_id_utils.ApiClientHelper.ModelReference:
    if print_format == 'list':
      formatter.AddColumns(('Id', 'Model Type', 'Labels', 'Creation Time'))
    if print_format == 'show':
      formatter.AddColumns((
          'Id',
          'Model Type',
          'Feature Columns',
          'Label Columns',
          'Labels',
          'Creation Time',
          'Expiration Time',
      ))
      if 'encryptionConfiguration' in object_info:
        formatter.AddColumns(('kmsKeyName',))
  elif reference_type == bq_id_utils.ApiClientHelper.RoutineReference:
    if print_format == 'list':
      formatter.AddColumns(('Id', 'Routine Type', 'Language', 'Creation Time',
                            'Last Modified Time'))
      formatter.AddColumns(('Is Remote',))
    if print_format == 'show':
      formatter.AddColumns((
          'Id',
          'Routine Type',
          'Language',
          'Signature',
          'Definition',
          'Creation Time',
          'Last Modified Time',
      ))
      if 'remoteFunctionOptions' in object_info:
        formatter.AddColumns((
            'Remote Function Endpoint',
            'Connection',
            'User Defined Context',
        ))
      if 'sparkOptions' in object_info:
        formatter.AddColumns((
            'Connection',
            'Runtime Version',
            'Container Image',
            'Properties',
            'Main File URI',
            'Main Class',
            'PyFile URIs',
            'Jar URIs',
            'File URIs',
            'Archive URIs',
        ))
  elif reference_type == bq_id_utils.ApiClientHelper.RowAccessPolicyReference:
    if print_format == 'list':
      formatter.AddColumns(('Id', 'Filter Predicate', 'Grantees',
                            'Creation Time', 'Last Modified Time'))
  elif reference_type == bq_id_utils.ApiClientHelper.TableReference:
    if print_format == 'list':
      formatter.AddColumns((
          'tableId',
          'Type',
      ))
      formatter.AddColumns(
          ('Labels', 'Time Partitioning', 'Clustered Fields'))
    if print_format == 'show':
      use_default = True
      if object_info is not None:
        if object_info['type'] == 'VIEW':
          formatter.AddColumns(
              ('Last modified', 'Schema', 'Type', 'Expiration'))
          use_default = False
        elif object_info['type'] == 'EXTERNAL':
          formatter.AddColumns(
              ('Last modified', 'Schema', 'Type', 'Total URIs', 'Expiration'))
          use_default = False
        elif 'snapshotDefinition' in object_info:
          formatter.AddColumns(('Base Table', 'Snapshot TimeStamp'))
        elif 'cloneDefinition' in object_info:
          formatter.AddColumns(('Base Table', 'Clone TimeStamp'))
      if use_default:
        # Other potentially available columns are: 'Long-Term Logical Bytes',
        # 'Active Logical Bytes', 'Total Partitions', 'Active Physical Bytes',
        # 'Long-Term Physical Bytes', 'Time Travel Bytes'.
        formatter.AddColumns((
            'Last modified',
            'Schema',
            'Total Rows',
            'Total Bytes',
            'Expiration',
            'Time Partitioning',
            'Clustered Fields',
            'Total Logical Bytes',
            'Total Physical Bytes',
        ))
      formatter.AddColumns(('Labels',))
      if 'encryptionConfiguration' in object_info:
        formatter.AddColumns(('kmsKeyName',))
      if 'resourceTags' in object_info:
        formatter.AddColumns(('Tags',))
    if print_format == 'view':
      formatter.AddColumns(('Query',))
    if print_format == 'materialized_view':
      formatter.AddColumns((
          'Query',
          'Enable Refresh',
          'Refresh Interval Ms',
          'Last Refresh Time'
      ))
    if print_format == 'table_replica':
      formatter.AddColumns((
          'Type',
          'Last modified',
          'Schema',
          'Source Table',
          'Source Last Refresh Time',
          'Replication Interval Seconds',
          'Replication Status',
          'Replication Error',
      ))
  elif reference_type == bq_id_utils.ApiClientHelper.EncryptionServiceAccount:
    formatter.AddColumns(list(object_info.keys()))
  elif reference_type == bq_id_utils.ApiClientHelper.ReservationReference:
    formatter.AddColumns((
        'name',
        'slotCapacity',
        'targetJobConcurrency',
        'ignoreIdleSlots',
        'creationTime',
        'updateTime',
        'multiRegionAuxiliary',
        'edition',
        'autoscaleMaxSlots',
        'autoscaleCurrentSlots'))
  elif reference_type == bq_id_utils.ApiClientHelper.BetaReservationReference:
    formatter.AddColumns((
        'name',
        'slotCapacity',
        'targetJobConcurrency',
        'ignoreIdleSlots',
        'creationTime',
        'updateTime',
        'multiRegionAuxiliary'))
  elif (
      reference_type
      == bq_id_utils.ApiClientHelper.CapacityCommitmentReference
  ):
    formatter.AddColumns((
        'name',
        'slotCount',
        'plan',
        'renewalPlan',
        'state',
        'commitmentStartTime',
        'commitmentEndTime',
        'multiRegionAuxiliary',
        'edition',
        'isFlatRate',
    ))
  elif (
      reference_type
      == bq_id_utils.ApiClientHelper.BetaReservationAssignmentReference
  ):
    formatter.AddColumns(('name', 'jobType', 'assignee', 'priority'))
  elif (
      reference_type
      == bq_id_utils.ApiClientHelper.ReservationAssignmentReference
  ):
    formatter.AddColumns(('name', 'jobType', 'assignee'))
  elif reference_type == bq_id_utils.ApiClientHelper.ConnectionReference:
    formatter.AddColumns((
        'name',
        'friendlyName',
        'description',
        'Last modified',
        'type',
        'hasCredential',
        'properties',
    ))
  else:
    raise ValueError('Unknown reference type: %s' % (reference_type.__name__,))


def RaiseError(result):
  """Raises an appropriate BigQuery error given the json error result."""
  error = result.get('error', {}).get('errors', [{}])[0]
  raise bq_error.CreateBigqueryError(error, result, [])


def IsFailedJob(job):
  """Predicate to determine whether or not a job failed."""
  return 'errorResult' in job.get('status', {})


def RaiseIfJobError(job):
  """Raises a BigQueryError if the job is in an error state.

  Args:
    job: a Job resource.

  Returns:
    job, if it is not in an error state.

  Raises:
    bq_error.BigqueryError: A bq_error.BigqueryError instance
      based on the job's error description.
  """
  if IsFailedJob(job):
    error = job['status']['errorResult']
    error_ls = job['status'].get('errors', [])
    raise bq_error.CreateBigqueryError(
        error,
        error,
        error_ls,
        job_ref=str(bq_processor_utils.ConstructObjectReference(job)),
        session_id=bq_processor_utils.GetSessionId(job),
    )
  return job


def GetJobTypeName(job_info):
  """Helper for job printing code."""
  job_names = set(('extract', 'load', 'query', 'copy'))
  try:
    return set(job_info.get('configuration',
                            {}).keys()).intersection(job_names).pop()
  except KeyError:
    return None


def ProcessSources(source_string):
  """Take a source string and return a list of URIs.

  The list will consist of either a single local filename, which
  we check exists and is a file, or a list of gs:// uris.

  Args:
    source_string: A comma-separated list of URIs.

  Returns:
    List of one or more valid URIs, as strings.

  Raises:
    bq_error.BigqueryClientError: if no valid list of sources can be
      determined.
  """
  sources = [source.strip() for source in source_string.split(',')]
  gs_uris = [
      source
      for source in sources
      if source.startswith(bq_processor_utils.GCS_SCHEME_PREFIX)
  ]
  if not sources:
    raise bq_error.BigqueryClientError('No sources specified')
  if gs_uris:
    if len(gs_uris) != len(sources):
      raise bq_error.BigqueryClientError(
          'All URIs must begin with "{}" if any do.'.format(
              bq_processor_utils.GCS_SCHEME_PREFIX))
    return sources
  else:
    source = sources[0]
    if len(sources) > 1:
      raise bq_error.BigqueryClientError(
          'Local upload currently supports only one file, found %d' %
          (len(sources),))
    if not os.path.exists(source):
      raise bq_error.BigqueryClientError(
          'Source file not found: %s' % (source,))
    if not os.path.isfile(source):
      raise bq_error.BigqueryClientError(
          'Source path is not a file: %s' % (source,))
  return sources


def ReadSchema(schema: str) -> List[str]:
  """Create a schema from a string or a filename.

  If schema does not contain ':' and is the name of an existing
  file, read it as a JSON schema. If not, it must be a
  comma-separated list of fields in the form name:type.

  Args:
    schema: A filename or schema.

  Returns:
    The new schema (as a dict).

  Raises:
    bq_error.BigquerySchemaError: If the schema is invalid or the
      filename does not exist.
  """

  if schema.startswith(bq_processor_utils.GCS_SCHEME_PREFIX):
    raise bq_error.BigquerySchemaError(
        'Cannot load schema files from GCS.')

  def NewField(entry):
    name, _, field_type = entry.partition(':')
    if entry.count(':') > 1 or not name.strip():
      raise bq_error.BigquerySchemaError(
          'Invalid schema entry: %s' % (entry,))
    return {
        'name': name.strip(),
        'type': field_type.strip().upper() or 'STRING',
    }

  if not schema:
    raise bq_error.BigquerySchemaError('Schema cannot be empty')
  elif os.path.exists(schema):
    with open(schema) as f:
      try:
        loaded_json = json.load(f)
      except ValueError as e:
        raise bq_error.BigquerySchemaError(
            (
                'Error decoding JSON schema from file %s: %s\n'
                'To specify a one-column schema, use "name:string".'
            )
            % (schema, e)
        )
    if not isinstance(loaded_json, list):
      raise bq_error.BigquerySchemaError(
          'Error in "%s": Table schemas must be specified as JSON lists.' %
          schema)
    return loaded_json
  elif re.match(r'[./\\]', schema) is not None:
    # We have something that looks like a filename, but we didn't
    # find it. Tell the user about the problem now, rather than wait
    # for a round-trip to the server.
    raise bq_error.BigquerySchemaError(
        'Error reading schema: "%s" looks like a filename, but was not found.'
        % (schema,)
    )
  else:
    return [NewField(entry) for entry in schema.split(',')]


def FormatInfoByType(object_info, object_type):
  """Format a single object_info (based on its 'kind' attribute)."""
  if object_type == bq_id_utils.ApiClientHelper.JobReference:
    return FormatJobInfo(object_info)
  elif object_type == bq_id_utils.ApiClientHelper.ProjectReference:
    return FormatProjectInfo(object_info)
  elif object_type == bq_id_utils.ApiClientHelper.DatasetReference:
    return FormatDatasetInfo(object_info)
  elif object_type == bq_id_utils.ApiClientHelper.TableReference:
    return FormatTableInfo(object_info)
  elif object_type == bq_id_utils.ApiClientHelper.ModelReference:
    return FormatModelInfo(object_info)
  elif object_type == bq_id_utils.ApiClientHelper.RoutineReference:
    return FormatRoutineInfo(object_info)
  elif object_type == bq_id_utils.ApiClientHelper.RowAccessPolicyReference:
    return FormatRowAccessPolicyInfo(object_info)
  elif object_type == bq_id_utils.ApiClientHelper.TransferConfigReference:
    return FormatTransferConfigInfo(object_info)
  elif object_type == bq_id_utils.ApiClientHelper.TransferRunReference:
    return FormatTransferRunInfo(object_info)
  elif object_type == bq_id_utils.ApiClientHelper.TransferLogReference:
    return FormatTransferLogInfo(object_info)
  elif object_type == bq_id_utils.ApiClientHelper.EncryptionServiceAccount:
    return object_info
  elif issubclass(
      object_type, bq_id_utils.ApiClientHelper.ReservationReference
  ):
    return FormatReservationInfo(
        reservation=object_info, reference_type=object_type
    )
  elif issubclass(
      object_type, bq_id_utils.ApiClientHelper.CapacityCommitmentReference
  ):
    return FormatCapacityCommitmentInfo(object_info)
  elif issubclass(
      object_type, bq_id_utils.ApiClientHelper.ReservationAssignmentReference
  ):
    return FormatReservationAssignmentInfo(object_info)
  elif object_type == bq_id_utils.ApiClientHelper.ConnectionReference:
    return FormatConnectionInfo(object_info)
  else:
    raise ValueError('Unknown object type: %s' % (object_type,))


def FormatJobInfo(job_info):
  """Prepare a job_info for printing.

  Arguments:
    job_info: Job dict to format.

  Returns:
    The new job_info.
  """
  result = job_info.copy()
  reference = bq_processor_utils.ConstructObjectReference(result)
  result.update(dict(reference))
  stats = result.get('statistics', {})

  result['Job Type'] = GetJobTypeName(result)

  result['State'] = result['status']['state']
  if 'user_email' in result:
    result['User Email'] = result['user_email']
  if result['State'] == 'DONE':
    try:
      RaiseIfJobError(result)
      result['State'] = 'SUCCESS'
    except bq_error.BigqueryError:
      result['State'] = 'FAILURE'

  if 'startTime' in stats:
    start = int(stats['startTime']) / 1000
    if 'endTime' in stats:
      duration_seconds = int(stats['endTime']) / 1000 - start
      result['Duration'] = str(datetime.timedelta(seconds=duration_seconds))
    result['Start Time'] = FormatTime(start)


  session_id = bq_processor_utils.GetSessionId(job_info)
  if session_id:
    result['Session Id'] = session_id

  query_stats = stats.get('query', {})
  if 'totalBytesProcessed' in query_stats:
    result['Bytes Processed'] = query_stats['totalBytesProcessed']
  if 'totalBytesBilled' in query_stats:
    result['Bytes Billed'] = query_stats['totalBytesBilled']
  if 'billingTier' in query_stats:
    result['Billing Tier'] = query_stats['billingTier']
  config = result.get('configuration', {})
  if 'labels' in config:
    result['Labels'] = _FormatLabels(config['labels'])
  if 'numDmlAffectedRows' in query_stats:
    result['Affected Rows'] = query_stats['numDmlAffectedRows']
  if 'ddlOperationPerformed' in query_stats:
    result['DDL Operation Performed'] = query_stats['ddlOperationPerformed']
  if 'ddlTargetTable' in query_stats:
    result['DDL Target Table'] = dict(query_stats['ddlTargetTable'])
  if 'ddlTargetRoutine' in query_stats:
    result['DDL Target Routine'] = dict(query_stats['ddlTargetRoutine'])
  if 'ddlTargetRowAccessPolicy' in query_stats:
    result['DDL Target Row Access Policy'] = dict(
        query_stats['ddlTargetRowAccessPolicy'])
  if 'ddlAffectedRowAccessPolicyCount' in query_stats:
    result['DDL Affected Row Access Policy Count'] = query_stats[
        'ddlAffectedRowAccessPolicyCount']
  if 'statementType' in query_stats:
    result['Statement Type'] = query_stats['statementType']
    if query_stats['statementType'] == 'ASSERT':
      result['Assertion'] = True
  return result


def FormatProjectInfo(project_info):
  """Prepare a project_info for printing.

  Arguments:
    project_info: Project dict to format.

  Returns:
    The new project_info.
  """
  result = project_info.copy()
  reference = bq_processor_utils.ConstructObjectReference(result)
  result.update(dict(reference))
  return result


def FormatModelInfo(model_info):
  """Prepare a model for printing.

  Arguments:
    model_info: Model dict to format.

  Returns:
    A dictionary of model properties.
  """
  result = {}
  result['Id'] = model_info['modelReference']['modelId']
  result['Model Type'] = ''
  if 'modelType' in model_info:
    result['Model Type'] = model_info['modelType']
  if 'labels' in model_info:
    result['Labels'] = _FormatLabels(model_info['labels'])
  if 'creationTime' in model_info:
    result['Creation Time'] = FormatTime(
        int(model_info['creationTime']) / 1000)
  if 'expirationTime' in model_info:
    result['Expiration Time'] = FormatTime(
        int(model_info['expirationTime']) / 1000)
  if 'featureColumns' in model_info:
    result['Feature Columns'] = _FormatStandardSqlFields(
        model_info['featureColumns'])
  if 'labelColumns' in model_info:
    result['Label Columns'] = _FormatStandardSqlFields(
        model_info['labelColumns'])
  if 'encryptionConfiguration' in model_info:
    result['kmsKeyName'] = model_info['encryptionConfiguration']['kmsKeyName']
  return result


def FormatRoutineDataType(data_type):
  """Converts a routine data type to a pretty string representation.

  Arguments:
    data_type: Routine data type dict to format.

  Returns:
    A formatted string.
  """
  type_kind = data_type['typeKind']
  if type_kind == 'ARRAY':
    return '{}<{}>'.format(
        type_kind,
        FormatRoutineDataType(data_type['arrayElementType']))
  elif type_kind == 'STRUCT':
    struct_fields = [
        '{} {}'.format(field['name'], FormatRoutineDataType(field['type']))
        for field in data_type['structType']['fields']
    ]
    return '{}<{}>'.format(type_kind, ', '.join(struct_fields))
  else:
    return type_kind


def FormatRoutineTableType(table_type):
  """Converts a routine table type to a pretty string representation.

  Arguments:
    table_type: Routine table type dict to format.

  Returns:
    A formatted string.
  """
  columns = [
      '{} {}'.format(column['name'], FormatRoutineDataType(column['type']))
      for column in table_type['columns']
  ]
  return 'TABLE<{}>'.format(', '.join(columns))


def FormatRoutineArgumentInfo(routine_type, argument):
  """Converts a routine argument to a pretty string representation.

  Arguments:
    routine_type: The routine type of the corresponding routine. It's of
      string type corresponding to the string value of enum
      cloud.bigquery.v2.Routine.RoutineType.
    argument: Routine argument dict to format.

  Returns:
    A formatted string.
  """
  if 'dataType' in argument:
    display_type = FormatRoutineDataType(argument['dataType'])
  elif argument.get('argumentKind') == 'ANY_TYPE':
    display_type = 'ANY TYPE'

  if 'name' in argument:
    argument_mode = ''
    if 'mode' in argument:
      argument_mode = argument['mode'] + ' '
    if (
        routine_type == 'AGGREGATE_FUNCTION'
        and 'isAggregate' in argument
        and not argument['isAggregate']
    ):
      return '{}{} {} {}'.format(
          argument_mode, argument['name'], display_type, 'NOT AGGREGATE'
      )
    else:
      return '{}{} {}'.format(argument_mode, argument['name'], display_type)
  else:
    return display_type


def FormatRoutineInfo(routine_info):
  """Prepare a routine for printing.

  Arguments:
    routine_info: Routine dict to format.

  Returns:
    A dictionary of routine properties.
  """
  result = {}
  result['Id'] = routine_info['routineReference']['routineId']
  result['Routine Type'] = routine_info['routineType']
  result['Language'] = routine_info.get('language', '')
  signature = '()'
  return_type = routine_info.get('returnType')
  return_table_type = routine_info.get('returnTableType')
  if 'arguments' in routine_info:
    argument_list = routine_info['arguments']
    signature = '({})'.format(
        ', '.join(
            FormatRoutineArgumentInfo(
                routine_info['routineType'], argument
            )
            for argument in argument_list
        )
    )
  if return_type:
    signature = '{} -> {}'.format(
        signature, FormatRoutineDataType(return_type))
  if return_table_type:
    signature = '{} -> {}'.format(
        signature, FormatRoutineTableType(return_table_type))
  if return_type or return_table_type or ('arguments' in routine_info):
    result['Signature'] = signature
  if 'definitionBody' in routine_info:
    result['Definition'] = routine_info['definitionBody']
  if 'creationTime' in routine_info:
    result['Creation Time'] = FormatTime(
        int(routine_info['creationTime']) / 1000)
  if 'lastModifiedTime' in routine_info:
    result['Last Modified Time'] = FormatTime(
        int(routine_info['lastModifiedTime']) / 1000)
  result['Is Remote'] = 'No'
  if 'remoteFunctionOptions' in routine_info:
    result['Is Remote'] = 'Yes'
    result['Remote Function Endpoint'] = routine_info[
        'remoteFunctionOptions']['endpoint']
    result['Connection'] = routine_info['remoteFunctionOptions']['connection']
    result['User Defined Context'] = routine_info[
        'remoteFunctionOptions'].get('userDefinedContext', '')
  if 'sparkOptions' in routine_info:
    spark_options = routine_info['sparkOptions']
    options = [
        ('connection', 'Connection'),
        ('runtimeVersion', 'Runtime Version'),
        ('containerImage', 'Container Image'),
        ('properties', 'Properties'),
        ('mainFileUri', 'Main File URI'),
        ('mainClass', 'Main Class'),
        ('pyFileUris', 'PyFile URIs'),
        ('jarUris', 'Jar URIs'),
        ('fileUris', 'File URIs'),
        ('archiveUris', 'Archive URIs'),
    ]
    for spark_key, result_key in options:
      if spark_key in spark_options:
        result[result_key] = spark_options[spark_key]
  return result


def FormatRowAccessPolicyInfo(row_access_policy_info):
  """Prepare a row access policy for printing.

  Arguments:
    row_access_policy_info: Row access policy dict to format.

  Returns:
    A dictionary of row access policy properties.
  """
  result = {}
  result['Id'] = row_access_policy_info['rowAccessPolicyReference'][
      'policyId']
  result['Filter Predicate'] = row_access_policy_info['filterPredicate']
  result['Grantees'] = ', '.join(row_access_policy_info['grantees'])
  if 'creationTime' in row_access_policy_info:
    result['Creation Time'] = FormatTimeFromProtoTimestampJsonString(
        row_access_policy_info['creationTime']
    )
  if 'lastModifiedTime' in row_access_policy_info:
    result['Last Modified Time'] = FormatTimeFromProtoTimestampJsonString(
        row_access_policy_info['lastModifiedTime']
    )
  return result


def FormatDatasetInfo(dataset_info):
  """Prepare a dataset_info for printing.

  Arguments:
    dataset_info: Dataset dict to format.

  Returns:
    The new dataset_info.
  """
  result = dataset_info.copy()
  reference = bq_processor_utils.ConstructObjectReference(result)
  result.update(dict(reference))
  if 'lastModifiedTime' in result:
    result['Last modified'] = FormatTime(
        int(result['lastModifiedTime']) / 1000)
  if 'access' in result:
    result['ACLs'] = FormatAcl(result['access'])
  if 'labels' in result:
    result['Labels'] = _FormatLabels(result['labels'])
  if 'tags' in result:
    result['Tags'] = _FormatTags(result['tags'])
  if 'defaultEncryptionConfiguration' in result:
    result['kmsKeyName'] = result['defaultEncryptionConfiguration'][
        'kmsKeyName']
  if 'type' in result:
    result['Type'] = result['type']
    if result['type'] == 'LINKED' and 'linkedDatasetSource' in result:
      source_dataset = result['linkedDatasetSource']['sourceDataset']
      result['Source dataset'] = str(
          bq_id_utils.ApiClientHelper.DatasetReference.Create(
              **source_dataset
          )
      )
    if result['type'] == 'EXTERNAL' and 'externalDatasetReference' in result:
      external_dataset_reference = result['externalDatasetReference']
      if 'external_source' in external_dataset_reference:
        result['External source'] = external_dataset_reference[
            'external_source'
        ]
      if 'connection' in external_dataset_reference:
        result['Connection'] = external_dataset_reference['connection']
  if 'maxTimeTravelHours' in result:
    result['Max time travel (Hours)'] = result['maxTimeTravelHours']
  return result


def FormatTableInfo(table_info):
  """Prepare a table_info for printing.

  Arguments:
    table_info: Table dict to format.

  Returns:
    The new table_info.
  """
  result = table_info.copy()
  reference = bq_processor_utils.ConstructObjectReference(result)
  result.update(dict(reference))
  if 'lastModifiedTime' in result:
    result['Last modified'] = FormatTime(
        int(result['lastModifiedTime']) / 1000)
  if 'schema' in result:
    result['Schema'] = FormatSchema(result['schema'])
  if 'numBytes' in result:
    result['Total Bytes'] = result['numBytes']
  if 'numTotalLogicalBytes' in result:
    result['Total Logical Bytes'] = result['numTotalLogicalBytes']
  if 'numLongTermLogicalBytes' in result:
    result['Long-Term Logical Bytes'] = result['numLongTermLogicalBytes']
  if 'numActiveLogicalBytes' in result:
    result['Active Logical Bytes'] = result['numActiveLogicalBytes']
  if 'numPartitions' in result:
    result['Total Partitions'] = result['numPartitions']
  if 'numTotalPhysicalBytes' in result:
    result['Total Physical Bytes'] = result['numTotalPhysicalBytes']
  if 'numActivePhysicalBytes' in result:
    result['Active Physical Bytes'] = result['numActivePhysicalBytes']
  if 'numLongTermPhysicalBytes' in result:
    result['Long-Term Physical Bytes'] = result['numLongTermPhysicalBytes']
  if 'numTimeTravelBytes' in result:
    result['Time Travel Bytes'] = result['numTimeTravelBytes']
  if 'numRows' in result:
    result['Total Rows'] = result['numRows']
  if 'expirationTime' in result:
    result['Expiration'] = FormatTime(
        int(result['expirationTime']) / 1000)
  if 'labels' in result:
    result['Labels'] = _FormatLabels(result['labels'])
  if 'resourceTags' in result:
    result['Tags'] = _FormatResourceTags(result['resourceTags'])
  if 'timePartitioning' in result:
    if 'type' in result['timePartitioning']:
      result['Time Partitioning'] = result['timePartitioning']['type']
    else:
      result['Time Partitioning'] = 'DAY'
    extra_info = []
    if 'field' in result['timePartitioning']:
      partitioning_field = result['timePartitioning']['field']
      extra_info.append('field: %s' % partitioning_field)
    if 'expirationMs' in result['timePartitioning']:
      expiration_ms = int(result['timePartitioning']['expirationMs'])
      extra_info.append('expirationMs: %d' % (expiration_ms,))
    if extra_info:
      result['Time Partitioning'] += (' (%s)' % (', '.join(extra_info),))
  if 'clustering' in result:
    if 'fields' in result['clustering']:
      result['Clustered Fields'] = ', '.join(result['clustering']['fields'])
  if 'type' in result:
    result['Type'] = result['type']
    if 'view' in result and 'query' in result['view']:
      result['Query'] = result['view']['query']
    if 'materializedView' in result and 'query' in result['materializedView']:
      result['Query'] = result['materializedView']['query']
      if 'enableRefresh' in result['materializedView']:
        result['Enable Refresh'] = result['materializedView']['enableRefresh']
      if 'refreshIntervalMs' in result['materializedView']:
        result['Refresh Interval Ms'] = result['materializedView'][
            'refreshIntervalMs']
      if ('lastRefreshTime' in result['materializedView'] and
          result['materializedView']['lastRefreshTime'] != '0'):
        result['Last Refresh Time'] = FormatTime(
            int(result['materializedView']['lastRefreshTime']) / 1000)
    if 'tableReplicationInfo' in result:
      result['Source Table'] = _FormatTableReference(
          result['tableReplicationInfo']['sourceTable']
      )
      result['Replication Interval Seconds'] = int(
          int(result['tableReplicationInfo']['replicationIntervalMs']) / 1000
      )
      result['Replication Status'] = result['tableReplicationInfo'][
          'replicationStatus'
      ]
      if 'replicatedSourceLastRefreshTime' in result['tableReplicationInfo']:
        result['Source Last Refresh Time'] = FormatTime(
            int(
                result['tableReplicationInfo'][
                    'replicatedSourceLastRefreshTime'
                ]
            )
            / 1000
        )
      if 'replicationError' in result['tableReplicationInfo']:
        result['Replication Error'] = result['tableReplicationInfo'][
            'replicationError'
        ]['message']
    if result['type'] == 'EXTERNAL':
      if 'externalDataConfiguration' in result:
        result['Total URIs'] = len(
            result['externalDataConfiguration']['sourceUris'])
  if (
      'encryptionConfiguration' in result
      and 'kmsKeyName' in result['encryptionConfiguration']
  ):
    result['kmsKeyName'] = result['encryptionConfiguration']['kmsKeyName']
  if 'snapshotDefinition' in result:
    result['Base Table'] = result['snapshotDefinition']['baseTableReference']
    result['Snapshot TimeStamp'] = (
        FormatTimeFromProtoTimestampJsonString(
            result['snapshotDefinition']['snapshotTime']))
  if 'cloneDefinition' in result:
    result['Base Table'] = result['cloneDefinition']['baseTableReference']
    result['Clone TimeStamp'] = (
        FormatTimeFromProtoTimestampJsonString(
            result['cloneDefinition']['cloneTime']))
  return result




def FormatTransferConfigInfo(transfer_config_info):
  """Prepare transfer config info for printing.

  Arguments:
    transfer_config_info: transfer config info to format.

  Returns:
    The new transfer config info.
  """

  result = {}
  for key, value in transfer_config_info.items():
    result[key] = value

  return result


def FormatTransferLogInfo(transfer_log_info):
  """Prepare transfer log info for printing.

  Arguments:
    transfer_log_info: transfer log info to format.

  Returns:
    The new transfer config log.
  """
  result = {}
  for key, value in transfer_log_info.items():
    result[key] = value

  return result


def FormatTransferRunInfo(transfer_run_info):
  """Prepare transfer run info for printing.

  Arguments:
    transfer_run_info: transfer run info to format.

  Returns:
    The new transfer run info.
  """
  result = {}
  for key, value in transfer_run_info.items():
    if key in _COLUMNS_TO_INCLUDE_FOR_TRANSFER_RUN:
      result[key] = value
  return result


def FormatReservationInfo(reservation, reference_type):
  """Prepare a reservation for printing.

  Arguments:
    reservation: reservation to format.
    reference_type: Type of reservation.

  Returns:
    A dictionary of reservation properties.
  """
  result = {}
  for key, value in reservation.items():
    if key == 'name':
      project_id, location, reservation_id = ParseReservationPath(value)
      reference = bq_id_utils.ApiClientHelper.ReservationReference.Create(
          projectId=project_id,
          location=location,
          reservationId=reservation_id)
      result[key] = reference.__str__()
    else:
      result[key] = value
  # Default values not passed along in the response.
  if 'slotCapacity' not in list(result.keys()):
    result['slotCapacity'] = '0'
  if 'ignoreIdleSlots' not in list(result.keys()):
    result['ignoreIdleSlots'] = 'False'
  if 'multiRegionAuxiliary' not in list(result.keys()):
    result['multiRegionAuxiliary'] = 'False'
  if 'concurrency' in list(result.keys()):
    # Rename concurrency we get from the API to targetJobConcurrency.
    result['targetJobConcurrency'] = result['concurrency']
    result.pop('concurrency', None)
  else:
    result['targetJobConcurrency'] = '0 (auto)'
  if 'autoscale' in list(result.keys()):
    if 'maxSlots' in result['autoscale']:
      result['autoscaleMaxSlots'] = result['autoscale']['maxSlots']
      result['autoscaleCurrentSlots'] = '0'
      if 'currentSlots' in result['autoscale']:
        result['autoscaleCurrentSlots'] = result['autoscale']['currentSlots']
    # The original 'autoscale' fields is not needed anymore now.
    result.pop('autoscale', None)
  return result


def FormatCapacityCommitmentInfo(capacity_commitment):
  """Prepare a capacity commitment for printing.

  Arguments:
    capacity_commitment: capacity commitment to format.

  Returns:
    A dictionary of capacity commitment properties.
  """
  result = {}
  for key, value in capacity_commitment.items():
    if key == 'name':
      project_id, location, capacity_commitment_id = (
          ParseCapacityCommitmentPath(value)
      )
      reference = (
          bq_id_utils.ApiClientHelper.CapacityCommitmentReference.Create(
              projectId=project_id,
              location=location,
              capacityCommitmentId=capacity_commitment_id,
          )
      )
      result[key] = reference.__str__()
    else:
      result[key] = value
  # Default values not passed along in the response.
  if 'slotCount' not in list(result.keys()):
    result['slotCount'] = '0'
  if 'multiRegionAuxiliary' not in list(result.keys()):
    result['multiRegionAuxiliary'] = 'False'
  return result


def FormatReservationAssignmentInfo(reservation_assignment):
  """Prepare a reservation_assignment for printing.

  Arguments:
    reservation_assignment: reservation_assignment to format.

  Returns:
    A dictionary of reservation_assignment properties.
  """
  result = {}
  for key, value in reservation_assignment.items():
    if key == 'name':
      project_id, location, reservation_id, reservation_assignment_id = (
          _ParseReservationAssignmentPath(value)
      )
      reference = (
          bq_id_utils.ApiClientHelper.ReservationAssignmentReference.Create(
              projectId=project_id,
              location=location,
              reservationId=reservation_id,
              reservationAssignmentId=reservation_assignment_id,
          )
      )
      result[key] = reference.__str__()
    else:
      result[key] = value
  return result


def FormatConnectionInfo(connection):
  """Prepare a connection object for printing.

  Arguments:
    connection: connection to format.

  Returns:
    A dictionary of connection properties.
  """
  result = {}
  for key, value in connection.items():
    if key == 'name':
      project_id, location, connection_id = _ParseConnectionPath(value)
      reference = bq_id_utils.ApiClientHelper.ConnectionReference.Create(
          projectId=project_id, location=location, connectionId=connection_id)
      result[key] = reference.__str__()
    elif key == 'lastModifiedTime':
      result['Last modified'] = FormatTime(int(value) / 1000)
    elif key in CONNECTION_PROPERTY_TO_TYPE_MAP:
      result['type'] = CONNECTION_PROPERTY_TO_TYPE_MAP.get(key)
      result['properties'] = json.dumps(value)
    else:
      result[key] = value
  result['hasCredential'] = connection.get('hasCredential', False)
  return result


def NormalizeProjectReference(
    id_fallbacks: NamedTuple(
        'IDS',
        [
            ('project_id', Optional[str]),
        ],
    ),
    reference: bq_id_utils.ApiClientHelper.ProjectReference,
) -> bq_id_utils.ApiClientHelper.ProjectReference:
  if reference is None:
    try:
      return GetProjectReference(id_fallbacks=id_fallbacks)
    except bq_error.BigqueryClientError as e:
      raise bq_error.BigqueryClientError(
          'Project reference or a default project is required') from e
  return reference


def ExecuteInChunksWithProgress(request):
  """Run an apiclient request with a resumable upload, showing progress.

  Args:
    request: an apiclient request having a media_body that is a
      MediaFileUpload(resumable=True).

  Returns:
    The result of executing the request, if it succeeds.

  Raises:
    BigQueryError: on a non-retriable error or too many retriable errors.
  """
  result = None
  retriable_errors = 0
  output_token = None
  status = None
  while result is None:
    try:
      status, result = request.next_chunk()
    except googleapiclient.errors.HttpError as e:
      logging.error('HTTP Error %d during resumable media upload',
                    e.resp.status)
      # Log response headers, which contain debug info for GFEs.
      for key, value in e.resp.items():
        logging.info('  %s: %s', key, value)
      if e.resp.status in [502, 503, 504]:
        sleep_sec = 2**retriable_errors
        retriable_errors += 1
        if retriable_errors > 3:
          raise
        print('Error %d, retry #%d' % (e.resp.status, retriable_errors))
        time.sleep(sleep_sec)
        # Go around and try again.
      else:
        RaiseErrorFromHttpError(e)
    except (httplib2.HttpLib2Error, IOError) as e:
      RaiseErrorFromNonHttpError(e)
    if status:
      output_token = _OverwriteCurrentLine(
          'Uploaded %d%%... ' % int(status.progress() * 100), output_token)
  _OverwriteCurrentLine('Upload complete.', output_token)
  sys.stderr.write('\n')
  return result


class WaitPrinter:
  """Base class that defines the WaitPrinter interface."""

  def Print(self, job_id, wait_time, status):
    """Prints status for the current job we are waiting on.

    Args:
      job_id: the identifier for this job.
      wait_time: the number of seconds we have been waiting so far.
      status: the status of the job we are waiting for.
    """
    raise NotImplementedError('Subclass must implement Print')

  def Done(self):
    """Waiting is done and no more Print calls will be made.

    This function should handle the case of Print not being called.
    """
    raise NotImplementedError('Subclass must implement Done')


class WaitPrinterHelper(WaitPrinter):
  """A Done implementation that prints based off a property."""

  print_on_done = False

  def Done(self):
    if self.print_on_done:
      sys.stderr.write('\n')


class QuietWaitPrinter(WaitPrinterHelper):
  """A WaitPrinter that prints nothing."""

  def Print(self, unused_job_id, unused_wait_time, unused_status):
    pass


class VerboseWaitPrinter(WaitPrinterHelper):
  """A WaitPrinter that prints every update."""

  def __init__(self):
    self.output_token = None

  def Print(self, job_id, wait_time, status):
    self.print_on_done = True
    self.output_token = _OverwriteCurrentLine(
        'Waiting on %s ... (%ds) Current status: %-7s' %
        (job_id, wait_time, status), self.output_token)


class TransitionWaitPrinter(VerboseWaitPrinter):
  """A WaitPrinter that only prints status change updates."""

  _previous_status = None

  def Print(self, job_id, wait_time, status):
    if status != self._previous_status:
      self._previous_status = status
      super(TransitionWaitPrinter,
            self).Print(job_id, wait_time, status)
