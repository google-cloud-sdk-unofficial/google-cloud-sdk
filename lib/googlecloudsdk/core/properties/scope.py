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
"""Scope enum for the properties module."""

from googlecloudsdk.core.properties import exceptions


class InvalidScopeValueError(exceptions.Error):
  """Exception for when a string could not be parsed to a valid scope value."""

  def __init__(self, given):
    """Constructs a new exception.

    Args:
      given: str, The given string that could not be parsed.
    """
    super(InvalidScopeValueError, self).__init__(
        'Could not parse [{0}] into a valid configuration scope.  '
        'Valid values are [{1}]'.format(given, ', '.join(Scope.AllScopeNames()))
    )


class _ScopeInfo(object):

  # pylint: disable=redefined-builtin
  def __init__(self, id, description):
    self.id = id
    self.description = description


class Scope(object):
  """An enum class for the different types of property files that can be used."""

  INSTALLATION = _ScopeInfo(
      id='installation',
      description=(
          'The installation based configuration file applies to all users on'
          ' the system that use this version of the Cloud SDK.  If the SDK was'
          ' installed by an administrator, you will need administrator rights'
          ' to make changes to this file.'
      ),
  )
  USER = _ScopeInfo(
      id='user',
      description=(
          'The user based configuration file applies only to the '
          'current user of the system.  It will override any values from the '
          'installation configuration.'
      ),
  )

  _ALL = [USER, INSTALLATION]
  _ALL_SCOPE_NAMES = [s.id for s in _ALL]

  @staticmethod
  def AllValues():
    """Gets all possible enum values.

    Returns:
      [Scope], All the enum values.
    """
    return list(Scope._ALL)

  @staticmethod
  def AllScopeNames():
    return list(Scope._ALL_SCOPE_NAMES)

  @staticmethod
  def FromId(scope_id):
    """Gets the enum corresponding to the given scope id.

    Args:
      scope_id: str, The scope id to parse.

    Raises:
      InvalidScopeValueError: If the given value cannot be parsed.

    Returns:
      OperatingSystemTuple, One of the OperatingSystem constants or None if the
      input is None.
    """
    if not scope_id:
      return None
    for scope in Scope._ALL:
      if scope.id == scope_id:
        return scope
    raise InvalidScopeValueError(scope_id)

  @staticmethod
  def GetHelpString():
    return '\n\n'.join(
        ['*{0}*::: {1}'.format(s.id, s.description) for s in Scope.AllValues()]
    )
