# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Validators and constants for the properties module."""

import os
import re

from googlecloudsdk.core.properties.exceptions import InvalidValueError
from googlecloudsdk.core.properties.exceptions import PropertyValue
from googlecloudsdk.core.util import scaled_integer
import six


_VALID_PROJECT_REGEX = re.compile(
    r'^'
    # An optional domain-like component, ending with a colon, e.g.,
    # google.com:
    r'(?:(?:[-a-z0-9]{1,63}\.)*(?:[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?):)?'
    # Followed by a required identifier-like component, for example:
    #   waffle-house    match
    #   -foozle        no match
    #   Foozle         no match
    # We specifically disallow project number, even though some GCP backends
    # could accept them.
    # We also allow a leading digit as some legacy project ids can have
    # a leading digit.
    r'(?:(?:[a-z0-9](?:[-a-z0-9]{0,61}[a-z0-9])?))'
    r'$'
)

_VALID_ENDPOINT_OVERRIDE_REGEX = re.compile(
    r'^'
    # require http or https for scheme
    r'(?:https?)://'
    # netlocation portion of address. can be any of
    # - domain name
    # - 'localhost'
    # - ipv4 addr
    # - ipv6 addr
    r'(?:'  # begin netlocation
    # - domain name, e.g. 'test-foo.sandbox.googleapis.com', or 'localhost'
    r'(?:[A-Z0-9](?:[A-Z0-9-.])+)|'
    # - ipv4
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'
    # - ipv6
    r'\[?[A-F0-9]*:[A-F0-9:]+\]?'
    r')'  # end netlocation
    # optional port
    r'(?::\d+)?'
    # require trailing slash, fragment optional
    r'(?:/|[/?]\S+/)' r'$',
    re.IGNORECASE,
)

_GRPC_DIRECTPATH = (
    r'(?:(?:dns|google-c2p):///'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-.])+)|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'
    r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'
    r'(?::\d+)?(?:/|[/?]\S+/)?'
    r')'
)

_PURE_GRPC = (
    r'(?:'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-.])+)|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'
    r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'
    r'(?::\d+)'
    r')'
)

_HTTP_PATTERN = _VALID_ENDPOINT_OVERRIDE_REGEX.pattern[1:-1]  # strip ^ and $

_VALID_STORAGE_GRPC_ENDPOINT_OVERRIDE_REGEX = re.compile(
    r'^(?:'
    + _HTTP_PATTERN
    + r'|'
    + _GRPC_DIRECTPATH
    + r'|'
    + _PURE_GRPC
    + r')$',
    re.IGNORECASE,
)

_PUBSUB_NOTICE_URL = (
    'https://cloud.google.com/functions/docs/writing/background#event_parameter'
)

_B_468088880_FIXED = True


def Stringize(value):
  if isinstance(value, six.string_types):
    return value
  return str(value)


def ExistingAbsoluteFilepathValidator(file_path):
  """Checks to see if the file path exists and is an absolute path."""
  if file_path is None:
    return
  if not os.path.isfile(file_path):
    raise InvalidValueError('The provided path must exist.')
  if not os.path.isabs(file_path):
    raise InvalidValueError('The provided path must be absolute.')


def _LooksLikeAProjectName(project):
  """Heuristics testing if a string looks like a project name, but an id."""

  if re.match(r'[-0-9A-Z]', project[0]):
    return True

  return any(c in project for c in ' !"\'')


def _BooleanValidator(property_name, property_value):
  """Validates boolean properties.

  Args:
    property_name: str, the name of the property
    property_value: PropertyValue | str | bool, the value to validate

  Raises:
    InvalidValueError: if value is not boolean
  """
  accepted_strings = [
      'true',
      '1',
      'on',
      'yes',
      'y',
      'false',
      '0',
      'off',
      'no',
      'n',
      '',
      'none',
  ]
  if isinstance(property_value, PropertyValue):
    value = property_value.value
  else:
    value = property_value
  if Stringize(value).lower() not in accepted_strings:
    raise InvalidValueError(
        'The [{0}] value [{1}] is not valid. Possible values: [{2}]. '
        '(See http://yaml.org/type/bool.html)'.format(
            property_name,
            value,
            ', '.join([x if x else "''" for x in accepted_strings]),
        )
    )


def _IntegerValidator(property_name=None, property_value=None):
  """Validates integer properties.

  Args:
    property_name: str, the name of the property
    property_value: PropertyValue | int | str, the value to validate

  Raises:
    InvalidValueError: if value is not integer
  """
  if property_value is None:
    return
  if property_name is None:
    return

  if isinstance(property_value, PropertyValue):
    value = property_value.value
  else:
    value = property_value

  try:
    # Attempt to convert the value to an integer.
    int_value = int(value)

  except (ValueError, TypeError) as exc:

    raise InvalidValueError(
        f'The [{property_name}] value [{value}] is not valid. Only integer'
        ' values are allowed for this property.'
    ) from exc

  # Check if the converted value is an integer.

  if not isinstance(int_value, int):
    raise InvalidValueError(
        f'The [{property_name}] value [{value}] is not valid. Only integer'
        ' values are allowed for this property.'
    )

  # Ensure the integer value is positive.
  if int_value <= 0:

    raise InvalidValueError(
        f'The [{property_name}] value [{value}] is not valid. Only positive'
        ' integer values are allowed.'
    )


def _BuildTimeoutValidator(timeout):
  """Validates build timeouts."""
  # pylint: disable=g-import-not-at-top
  from googlecloudsdk.core.util import times
  # pylint: enable=g-import-not-at-top

  if timeout is None:
    return
  seconds = times.ParseDuration(timeout, default_suffix='s').total_seconds
  if seconds <= 0:
    raise InvalidValueError('Timeout must be a positive time duration.')


def _HumanReadableByteAmountValidator(size_string):
  """Validates human readable byte amounts, e.g. 1KiB."""
  if size_string is None:
    return
  try:
    scaled_integer.ParseInteger(size_string)
  except ValueError as e:
    raise InvalidValueError(str(e)) from e


_VALID_ASSERTIONS = ('readonly',)


def _AssertValidator(val):
  """Validates the assert property value.

  Args:
    val: str or None, The assert property value to validate.

  Raises:
    InvalidValueError: If the value is not a valid assertion.
  """
  if val is None:
    return
  if val not in _VALID_ASSERTIONS:
    raise InvalidValueError(
        f'The assert property value [{val}] is not valid. '
        f'Possible values: [{", ".join(_VALID_ASSERTIONS)}].'
    )


def _UserAgentHeaderValueValidator(value):
  """Validates user-agent header values to prevent header injection."""
  if value is None:
    return
  if not isinstance(value, six.string_types):
    raise InvalidValueError('Value must be a string.')
  if not value.strip():
    raise InvalidValueError('Value cannot be empty or whitespace only.')
  if re.search(r'[\r\n\0]', value):
    raise InvalidValueError(
        'Value cannot contain newline or control characters.'
    )
  try:
    value.encode('ascii')
  except (UnicodeEncodeError, UnicodeDecodeError) as exc:
    raise InvalidValueError(
        'Value must contain only ASCII characters.'
    ) from exc


def AccessPolicyValidator(policy):
  """Checks to see if the Access Policy string is valid."""
  if policy is None:
    return
  if not policy.isdigit():
    raise InvalidValueError(
        'The access_context_manager.policy property must be set '
        'to the policy number, not a string.'
    )
