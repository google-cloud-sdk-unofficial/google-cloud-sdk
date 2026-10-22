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
"""Core types for the properties module."""

import functools
import os

from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.properties.exceptions import InvalidValueError
from googlecloudsdk.core.properties.exceptions import NoSuchPropertyError
from googlecloudsdk.core.properties.exceptions import PropertyValue
from googlecloudsdk.core.properties.parsers import _GetBoolProperty
from googlecloudsdk.core.properties.parsers import _GetIntProperty
from googlecloudsdk.core.properties.parsers import _GetProperty
from googlecloudsdk.core.properties.parsers import _GetPropertyWithoutCallback
from googlecloudsdk.core.properties.parsers import _GetPropertyWithoutDefault
from googlecloudsdk.core.properties.validators import _BooleanValidator
from googlecloudsdk.core.properties.validators import Stringize
from googlecloudsdk.core.util import encoding
import six


class _Section(object):
  """Represents a section of the properties file that has related properties.

  Attributes:
    name: str, The name of the section.
    is_hidden: bool, True if the section is hidden, False otherwise.
  """

  def __init__(self, name, hidden=False):
    self.__name = name
    self.__is_hidden = hidden
    self.__properties = {}

  @property
  def name(self):
    return self.__name

  @property
  def is_hidden(self):
    return self.__is_hidden

  def __iter__(self):
    return iter(self.__properties.values())

  def __hash__(self):
    return hash(self.name)

  def __eq__(self, other):
    return self.name == other.name

  def __ne__(self, other):
    return self.name != other.name

  def __gt__(self, other):
    return self.name > other.name

  def __ge__(self, other):
    return self.name >= other.name

  def __lt__(self, other):
    return self.name < other.name

  def __le__(self, other):
    return self.name <= other.name

  #  pylint: disable=missing-docstring
  def _Add(
      self,
      name,
      help_text=None,
      internal=False,
      hidden=False,
      callbacks=None,
      default=None,
      validator=None,
      choices=None,
      completer=None,
      default_flag=None,
  ):
    prop = _Property(
        section=self.__name,
        name=name,
        help_text=help_text,
        internal=internal,
        hidden=(self.is_hidden or hidden),
        callbacks=callbacks,
        default=default,
        validator=validator,
        choices=choices,
        completer=completer,
        default_flag=default_flag,
    )
    self.__properties[name] = prop
    return prop

  def _AddBool(
      self,
      name,
      help_text=None,
      internal=False,
      hidden=False,
      callbacks=None,
      default=None,
  ):
    return self._Add(
        name=name,
        help_text=help_text,
        internal=internal,
        hidden=hidden,
        callbacks=callbacks,
        default=default,
        validator=functools.partial(_BooleanValidator, name),
        choices=('true', 'false'),
    )

  def Property(self, property_name):
    """Gets a property from this section, given its name.

    Args:
      property_name: str, The name of the desired property.

    Returns:
      Property, The property corresponding to the given name.


    Raises:
      NoSuchPropertyError: If the property is not known for this section.
    """
    try:
      return self.__properties[property_name]
    except KeyError as exc:
      raise NoSuchPropertyError(
          'Section [{s}] has no property [{p}].'.format(
              s=self.__name, p=property_name
          )
      ) from exc

  def HasProperty(self, property_name):
    """True iff section has given property.

    Args:
      property_name: str, The name of the property to check for membership.

    Returns:
      a boolean. True iff this section contains property_name.
    """
    return property_name in self.__properties

  def AllProperties(self, include_hidden=False):
    """Gets a list of all registered property names in this section.

    Args:
      include_hidden: bool, True to include hidden properties in the result.

    Returns:
      [str], The property names.
    """
    return [
        name
        for name, prop in six.iteritems(self.__properties)
        if include_hidden or not prop.is_hidden
    ]

  def AllValues(
      self,
      list_unset=False,
      include_hidden=False,
      properties_file=None,
      only_file_contents=False,
  ):
    """Gets all the properties and their values for this section.

    Args:
      list_unset: bool, If True, include unset properties in the result.
      include_hidden: bool, True to include hidden properties in the result. If
        a property has a value set but is hidden, it will be included regardless
        of this setting.
      properties_file: properties_file.PropertiesFile, the file to read settings
        from.  If None the active property file will be used.
      only_file_contents: bool, True if values should be taken only from the
        properties file, false if flags, env vars, etc. should be consulted too.
        Mostly useful for listing file contents.

    Returns:
      {str:str}, The dict of {property:value} for this section.
    """
    properties_file = (
        properties_file or named_configs.ActivePropertiesFile.Load()
    )

    result = {}
    for prop in self:
      if prop.is_internal:
        # Never show internal properties, ever.
        continue
      if (
          prop.is_hidden
          and not include_hidden
          and _GetPropertyWithoutCallback(prop, properties_file) is None
      ):
        continue

      if only_file_contents:
        value = properties_file.Get(prop.section, prop.name)
      else:
        property_value = _GetPropertyWithoutDefault(prop, properties_file)
        if property_value is None:
          value = None
        else:
          value = property_value.value

      if value is None:
        if not list_unset:
          # Never include if not set and not including unset values.
          continue
        if prop.is_hidden and not include_hidden:
          # If including unset values, exclude if hidden and not including
          # hidden properties.
          continue

      # Always include if value is set (even if hidden)
      result[prop.name] = value
    return result

  def AllPropertyValues(
      self,
      list_unset=False,
      include_hidden=False,
      properties_file=None,
      only_file_contents=False,
  ):
    """Gets all the properties and their values for this section.

    Args:
      list_unset: bool, If True, include unset properties in the result.
      include_hidden: bool, True to include hidden properties in the result. If
        a property has a value set but is hidden, it will be included regardless
        of this setting.
      properties_file: properties_file.PropertiesFile, the file to read settings
        from.  If None the active property file will be used.
      only_file_contents: bool, True if values should be taken only from the
        properties file, false if flags, env vars, etc. should be consulted too.
        Mostly useful for listing file contents.

    Returns:
      {str:PropertyValue}, The dict of {property:value} for this section.
    """
    properties_file = (
        properties_file or named_configs.ActivePropertiesFile.Load()
    )

    result = {}
    for prop in self:
      if prop.is_internal:
        # Never show internal properties, ever.
        continue
      if (
          prop.is_hidden
          and not include_hidden
          and _GetPropertyWithoutCallback(prop, properties_file) is None
      ):
        continue

      if only_file_contents:
        property_value = PropertyValue(
            properties_file.Get(prop.section, prop.name),
            PropertyValue.PropertySource.PROPERTY_FILE,
        )
      else:
        property_value = _GetPropertyWithoutDefault(prop, properties_file)

      if (property_value is None) or (property_value.value is None):
        if not list_unset:
          # Never include if not set and not including unset property_values.
          continue
        if prop.is_hidden and not include_hidden:
          # If including unset property_values, exclude if hidden and not
          # including hidden properties.
          continue

      # Always include if value is set (even if hidden)
      result[prop.name] = property_value
    return result


class _Property(object):
  """An individual property that can be gotten from the properties file.

  Attributes:
    section: str, The name of the section the property appears in, within the
      file.
    name: str, The name of the property.
    help_text: str, The man page help for what this property does.
    is_hidden: bool, True to hide this property from display for users that
      don't know about them.
    is_internal: bool, True to hide this property from display even if it is
      set. Internal properties are implementation details not meant to be set by
      users.
    callbacks: [func], A list of functions to be called, in order, if no value
      is found elsewhere.  The result of a callback will be shown in when
      listing properties (if the property is not hidden).
    completer: [func], a completer function
    default: str, A final value to use if no value is found after the callbacks.
      The default value is never shown when listing properties regardless of
      whether the property is hidden or not.
    default_flag: default_flag name to include in RequiredPropertyError if
      property fails on Get. This can be used for flags that are tightly coupled
      with a property.
    validator: func(str), A function that is called on the value when .Set()'d
      or .Get()'d. For valid values, the function should do nothing. For invalid
      values, it should raise InvalidValueError with an explanation of why it
      was invalid.
    choices: [str], The allowable values for this property.  This is included in
      the help text and used in tab completion.
  """

  def __init__(
      self,
      section,
      name,
      help_text=None,
      hidden=False,
      internal=False,
      callbacks=None,
      default=None,
      validator=None,
      choices=None,
      completer=None,
      default_flag=None,
  ):
    self.__section = section
    self.__name = name
    self.__help_text = help_text
    self.__hidden = hidden
    self.__internal = internal
    self.__callbacks = callbacks or []
    self.__default = default
    self.__validator = validator
    self.__choices = choices
    self.__completer = completer
    self.__default_flag = default_flag

  @property
  def section(self):
    return self.__section

  @property
  def name(self):
    return self.__name

  @property
  def help_text(self):
    return self.__help_text

  @property
  def is_hidden(self):
    return self.__hidden

  @property
  def is_internal(self):
    return self.__internal

  @property
  def default(self):
    return self.__default

  @property
  def callbacks(self):
    return self.__callbacks

  @property
  def choices(self):
    return self.__choices

  @property
  def completer(self):
    return self.__completer

  @property
  def default_flag(self):
    return self.__default_flag

  def __hash__(self):
    return hash(self.section) + hash(self.name)

  def __eq__(self, other):
    return self.section == other.section and self.name == other.name

  def __ne__(self, other):
    return not self == other

  def __gt__(self, other):
    return self.name > other.name

  def __ge__(self, other):
    return self.name >= other.name

  def __lt__(self, other):
    return self.name < other.name

  def __le__(self, other):
    return self.name <= other.name

  def GetOrFail(self):
    """Shortcut for Get(required=True).

    Convenient as a callback function.

    Returns:
      str, The value for this property.
    Raises:
      RequiredPropertyError if property is not set.
    """

    return self.Get(required=True)

  def Get(self, required=False, validate=True):
    """Gets the value for this property.

    Looks first in the environment, then in the workspace config, then in the
    global config, and finally at callbacks.

    Args:
      required: bool, True to raise an exception if the property is not set.
      validate: bool, Whether or not to run the fetched value through the
        validation function.

    Returns:
      str, The value for this property.
    """
    property_value = self.GetPropertyValue(required, validate)
    if property_value is None:
      return None
    return Stringize(property_value.value)

  def GetPropertyValue(self, required=False, validate=True):
    """Gets the value for this property.

    Looks first in the environment, then in the workspace config, then in the
    global config, and finally at callbacks.

    Args:
      required: bool, True to raise an exception if the property is not set.
      validate: bool, Whether or not to run the fetched value through the
        validation function.

    Returns:
      PropertyValue, The value for this property.
    """
    property_value = _GetProperty(
        self, named_configs.ActivePropertiesFile.Load(), required
    )
    if validate:
      self.Validate(property_value)
    return property_value

  def IsExplicitlySet(self):
    """Determines if this property has been explicitly set by the user.

    Properties with defaults or callbacks don't count as explicitly set.

    Returns:
      True, if the value was explicitly set, False otherwise.
    """
    property_value = _GetPropertyWithoutCallback(
        self, named_configs.ActivePropertiesFile.Load()
    )
    if property_value is None:
      return False
    return property_value.value is not None

  def Validate(self, property_value):
    """Test to see if the value is valid for this property.

    Args:
      property_value: str | PropertyValue, The value of the property to be
        validated.

    Raises:
      InvalidValueError: If the value was invalid according to the property's
          validator.
    """
    if self.__validator:
      if isinstance(property_value, PropertyValue):
        value = property_value.value
      else:
        value = property_value
      try:
        self.__validator(value)
      except InvalidValueError as e:
        prop = '{}/{}'.format(self.section, self.name)
        error = 'Invalid value for property [{}]: {}'.format(prop, e)
        raise InvalidValueError(error) from e

  def GetBool(self, required=False, validate=True):
    """Gets the boolean value for this property.

    Looks first in the environment, then in the workspace config, then in the
    global config, and finally at callbacks.

    Does not validate by default because boolean properties were not previously
    validated, and startup functions rely on boolean properties that may have
    invalid values from previous installations

    Args:
      required: bool, True to raise an exception if the property is not set.
      validate: bool, Whether or not to run the fetched value through the
        validation function.

    Returns:
      bool, The boolean value for this property, or None if it is not set.

    Raises:
      InvalidValueError: if value is not boolean
    """
    value = _GetBoolProperty(
        self,
        named_configs.ActivePropertiesFile.Load(),
        required,
        validate=validate,
    )
    return value

  def GetInt(self, required=False, validate=True):
    """Gets the integer value for this property.

    Looks first in the environment, then in the workspace config, then in the
    global config, and finally at callbacks.

    Args:
      required: bool, True to raise an exception if the property is not set.
      validate: bool, Whether or not to run the fetched value through the
        validation function.

    Returns:
      int, The integer value for this property.
    """
    value = _GetIntProperty(
        self, named_configs.ActivePropertiesFile.Load(), required
    )
    if validate:
      self.Validate(value)
    return value

  def Set(self, property_value):
    """Sets the value for this property as an environment variable.

    Args:
      property_value: PropertyValue | str | bool, The proposed value for this
        property.  If None, it is removed from the environment.
    """
    self.Validate(property_value)
    if isinstance(property_value, PropertyValue):
      value = property_value.value
    else:
      value = property_value
    if value is not None:
      value = Stringize(value)
    encoding.SetEncodedValue(os.environ, self.EnvironmentName(), value)

  def AddCallback(self, callback):
    """Adds another callback for this property."""
    self.__callbacks.append(callback)

  def RemoveCallback(self, callback):
    """Removes given callback for this property."""
    self.__callbacks.remove(callback)

  def ClearCallback(self):
    """Removes all callbacks for this property."""
    self.__callbacks[:] = []

  def EnvironmentName(self):
    """Get the name of the environment variable for this property.

    Returns:
      str, The name of the correct environment variable.
    """
    return 'CLOUDSDK_{section}_{name}'.format(
        section=self.__section.upper(),
        name=self.__name.upper(),
    )

  def __str__(self):
    return '{section}/{name}'.format(section=self.__section, name=self.__name)
