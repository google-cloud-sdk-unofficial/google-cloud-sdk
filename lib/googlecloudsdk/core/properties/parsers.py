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
"""Parsers and property resolution helpers."""

import os
import sys

from googlecloudsdk.core import config
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.configurations import properties_file as prop_files_lib
from googlecloudsdk.core.properties.exceptions import InvalidValueError
from googlecloudsdk.core.properties.exceptions import MissingInstallationConfig
from googlecloudsdk.core.properties.exceptions import PropertyValue
from googlecloudsdk.core.properties.exceptions import RequiredPropertyError
from googlecloudsdk.core.properties.scope import Scope
from googlecloudsdk.core.properties.validators import _BooleanValidator
from googlecloudsdk.core.properties.validators import Stringize
from googlecloudsdk.core.util import encoding
import six


class _ValueFlag(object):
  """Container for a property value and the CLI flag that set it."""

  def __init__(self, value, flag):
    self.value = value
    self.flag = flag


class _InvocationStack(object):
  """Encapsulates the stack of CLI flag overrides during command execution."""

  def __init__(self):
    self._stack = [{}]

  def Push(self):
    self._stack.append({})

  def Pop(self):
    self._stack.pop()

  def GetStack(self):
    return self._stack

  def GetLatest(self):
    return self._stack[-1]

  def SetValue(self, prop, value, flag):
    value_flags = self.GetLatest()
    if value:
      prop.Validate(value)
    value_flags[prop] = _ValueFlag(value, flag)


# Singleton instance of the invocation stack for the process/runtime
INVOCATION_STACK = _InvocationStack()


def PersistProperty(prop, value, scope=None):
  """Sets the given property in the properties file.

  This function should not generally be used as part of normal program
  execution.  The property files are user editable config files that they should
  control.  This is mostly for initial setup of properties that get set during
  SDK installation.

  Args:
    prop: properties.Property, The property to set.
    value: str, The value to set for the property. If None, the property is
      removed.
    scope: Scope, The config location to set the property in.  If given, only
      this location will be updated and it is an error if that location does not
      exist.  If not given, it will attempt to update the property in the first
      of the following places that exists: - the active named config - user
      level config It will never fall back to installation properties; you must
      use that scope explicitly to set that value.

  Raises:
    MissingInstallationConfig: If you are trying to set the installation config,
      but there is not SDK root.
  """
  prop.Validate(value)
  if six.PY3:
    value = _EscapePercentSign(value)
  if scope == Scope.INSTALLATION:
    config.EnsureSDKWriteAccess()
    config_file = config.Paths().installation_properties_path
    if not config_file:
      raise MissingInstallationConfig()
    prop_files_lib.PersistProperty(config_file, prop.section, prop.name, value)
    named_configs.ActivePropertiesFile.Invalidate(mark_changed=True)
  else:
    active_config = named_configs.ConfigurationStore.ActiveConfig()
    active_config.PersistProperty(prop.section, prop.name, value)
  # Print message if value being set/unset is overridden by environment var
  # to prevent user confusion
  env_name = prop.EnvironmentName()
  override = encoding.GetEncodedValue(os.environ, env_name)
  if override:
    warning_message = (
        'WARNING: Property [{0}] is overridden '
        'by environment setting [{1}={2}]\n'
    )
    # Writing to sys.stderr because of circular dependency
    # in googlecloudsdk.core.log on properties
    sys.stderr.write(warning_message.format(prop.name, env_name, override))


def _GetProperty(prop, properties_file, required):
  """Gets the given property.

  If the property has a designated command line argument and args is provided,
  check args for the value first. If the corresponding environment variable is
  set, use that second. If still nothing, use the callbacks.

  Args:
    prop: properties.Property, The property to get.
    properties_file: properties_file.PropertiesFile, An already loaded
      properties files to use.
    required: bool, True to raise an exception if the property is not set.

  Raises:
    RequiredPropertyError: If the property was required but unset.

  Returns:
    PropertyValue, The value of the property, or None if it is not set.
  """

  flag_to_use = None

  invocation_stack = INVOCATION_STACK.GetStack()
  if len(invocation_stack) > 1:
    # First item is the blank stack entry, second is from the user command args.
    first_invocation = invocation_stack[1]
    if prop in first_invocation:
      flag_to_use = first_invocation.get(prop).flag

  property_value = _GetPropertyWithoutDefault(prop, properties_file)
  if property_value is not None and property_value.value is not None:
    return property_value

  # Still nothing, check the final default.
  if prop.default is not None:
    return PropertyValue(
        Stringize(prop.default), PropertyValue.PropertySource.DEFAULT
    )

  # Not set, throw if required.
  if required:
    raise RequiredPropertyError(prop, flag=flag_to_use)

  return None


def _GetPropertyWithoutDefault(prop, properties_file):
  """Gets the given property without using a default.

  If the property has a designated command line argument and args is provided,
  check args for the value first. If the corresponding environment variable is
  set, use that second. Next, return whatever is in the property file.  Finally,
  use the callbacks to find values.  Do not check the default value.

  Args:
    prop: properties.Property, The property to get.
    properties_file: properties_file.PropertiesFile, An already loaded
      properties files to use.

  Returns:
    PropertyValue, The value of the property, or None if it is not set.
  """
  # Try to get a value from args, env, or property file.
  property_value = _GetPropertyWithoutCallback(prop, properties_file)
  if property_value and property_value.value is not None:
    return property_value

  # No value, try getting a value from the callbacks.
  for callback in prop.callbacks:
    value = callback()
    if value is not None:
      return PropertyValue(
          Stringize(value), PropertyValue.PropertySource.CALLBACK
      )

  return None


def _GetPropertyWithoutCallback(prop, properties_file):
  """Gets the given property without using a callback or default.

  If the property has a designated command line argument and args is provided,
  check args for the value first. If the corresponding environment variable is
  set, use that second. Finally, return whatever is in the property file.  Do
  not check for values in callbacks or defaults.

  Args:
    prop: properties.Property, The property to get.
    properties_file: PropertiesFile, An already loaded properties files to use.

  Returns:
    PropertyValue, The value of the property, or None if it is not set.
  """
  # Look for a value in the flags that were used on this command.
  invocation_stack = INVOCATION_STACK.GetStack()
  for value_flags in reversed(invocation_stack):
    if prop not in value_flags:
      continue
    value_flag = value_flags.get(prop, None)
    if not value_flag:
      continue
    if value_flag.value is not None:
      return PropertyValue(
          Stringize(value_flag.value), PropertyValue.PropertySource.FLAG
      )

  # Check the environment variable overrides.
  value = encoding.GetEncodedValue(os.environ, prop.EnvironmentName())
  if value is not None:
    return PropertyValue(
        Stringize(value), PropertyValue.PropertySource.ENVIRONMENT
    )

  # Check the property file itself.
  value = properties_file.Get(prop.section, prop.name)
  if value is not None:
    return PropertyValue(
        Stringize(value), PropertyValue.PropertySource.PROPERTY_FILE
    )

  return None


def _GetBoolProperty(prop, properties_file, required, validate=False):
  """Gets the given property in bool form.

  Args:
    prop: properties.Property, The property to get.
    properties_file: properties_file.PropertiesFile, An already loaded
      properties files to use.
    required: bool, True to raise an exception if the property is not set.
    validate: bool, True to validate the value

  Returns:
    bool, The value of the property, or None if it is not set.
  """
  property_value = _GetProperty(prop, properties_file, required)
  if validate:
    _BooleanValidator(prop.name, property_value)
  if property_value is None or property_value.value is None:
    return None
  property_string_value = Stringize(property_value.value).lower()
  if property_string_value == 'none':
    return None
  return property_string_value in ['1', 'true', 'on', 'yes', 'y']


def _GetIntProperty(prop, properties_file, required):
  """Gets the given property in integer form.

  Args:
    prop: properties.Property, The property to get.
    properties_file: properties_file.PropertiesFile, An already loaded
      properties files to use.
    required: bool, True to raise an exception if the property is not set.

  Returns:
    int, The integer value of the property, or None if it is not set.
  """
  property_value = _GetProperty(prop, properties_file, required)
  if property_value is None or property_value.value is None:
    return None
  try:
    return int(property_value.value)
  except ValueError as exc:
    raise InvalidValueError(
        'The property [{prop}] must have an integer value: [{value}]'.format(
            prop=prop, value=property_value.value
        )
    ) from exc


def _EscapePercentSign(value):
  """Escape '%' in property value.

  Do nothing if value contains '%%', i.e. value was escaped by user.

  Args:
    value: property value

  Returns:
    str, value with escaped % sign
  """
  if not isinstance(value, six.string_types) or '%%' in value:
    return value
  elif '%' in value:
    return value.replace('%', '%%')
  else:
    return value
