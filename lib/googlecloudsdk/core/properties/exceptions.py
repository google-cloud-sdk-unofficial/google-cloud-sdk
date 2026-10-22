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
"""Exceptions for the properties module."""

import enum
from googlecloudsdk.core import exceptions
import six


_SET_PROJECT_HELP = """\
To set your project, run:

  $ gcloud config set project PROJECT_ID

or to unset it, run:

  $ gcloud config unset project"""


class Error(exceptions.Error):
  """Exceptions for the properties module."""


class PropertiesParseError(Error):
  """An exception to be raised when a properties file is invalid."""


class NoSuchPropertyError(Error):
  """An exception to be raised when the desired property does not exist."""


class MissingInstallationConfig(Error):
  """An exception to be raised when the sdk root does not exist."""

  def __init__(self):
    super(MissingInstallationConfig, self).__init__(
        'Installation properties could not be set because the installation '
        'root of the Cloud SDK could not be found.'
    )


class InvalidValueError(Error):
  """An exception to be raised when the set value of a property is invalid."""


class InvalidProjectError(Error):
  """An exception for bad project names, with a little user help."""

  def __init__(self, given):
    super(InvalidProjectError, self).__init__(given + '\n' + _SET_PROJECT_HELP)


class RequiredPropertyError(Error):
  """Generic exception for when a required property was not set."""

  FLAG_STRING = (
      'It can be set on a per-command basis by re-running your '
      'command with the [{flag}] flag.\n\n'
  )

  DEFAULT_SECTION_NAME = 'core'

  def __init__(self, prop, flag=None, extra_msg=None):
    if prop.section != RequiredPropertyError.DEFAULT_SECTION_NAME:
      section = prop.section + '/'
    else:
      section = ''

    flag = flag or prop.default_flag
    if flag:
      flag_msg = RequiredPropertyError.FLAG_STRING.format(flag=flag)
    else:
      flag_msg = ''

    msg = """\
The required property [{property_name}] is not currently set.
{flag_msg}You may set it for your current workspace by running:

  $ gcloud config set {section}{property_name} VALUE

or it can be set temporarily by the environment variable [{env_var}]""".format(
        property_name=prop.name,
        flag_msg=flag_msg,
        section=section,
        env_var=prop.EnvironmentName(),
    )
    if extra_msg:
      msg += '\n\n' + extra_msg
    super(RequiredPropertyError, self).__init__(msg)
    self.property = prop


class UnknownFormatError(exceptions.Error):
  """Unknown format name exception."""

  def __init__(self, printer_name, supported_formats):
    """Constructs a new exception.

    Args:
      printer_name: str, The unknown printer format.
      supported_formats: [str], Supported printer formats.
    """
    super(UnknownFormatError, self).__init__("""\
Format must be one of {0}; received [{1}].

For information on output formats:
  $ gcloud topic formats
""".format(', '.join(supported_formats), printer_name))


class PropertyValue(object):
  """Represents a value and source for a property.

  Attributes:
    value: any, the value of the property.
    source: enum, where the value was sourced from, or UNKNOWN.
  """

  class PropertySource(enum.Enum):
    UNKNOWN = 'unknown'
    PROPERTY_FILE = 'property file'
    ENVIRONMENT = 'environment'
    FLAG = 'flag'
    CALLBACK = 'callback'
    DEFAULT = 'default'

  def __init__(self, value, source=PropertySource.UNKNOWN):
    self.value = value
    self.source = source

  def __str__(self):
    return '{0} ({1})'.format(six.text_type(self.value), self.source.value)
