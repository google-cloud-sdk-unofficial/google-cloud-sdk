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

"""argparse actions that store values in properties."""

import argparse
import os
from typing import Any

from googlecloudsdk.core import properties


def StoreProperty(prop: properties._Property) -> type[argparse.Action]:
  """Get an argparse action that stores a value in a property.

  Also stores the value in the namespace object, like the default action. The
  value is stored in the invocation stack, rather than persisted permanently.

  Args:
    prop: The property that should get the invocation value.

  Returns:
    An argparse action that routes the value correctly.
  """

  class Action(argparse.Action):
    """The action created for StoreProperty."""

    # store_property is referenced in calliope.parser_arguments.add_argument
    store_property = (prop, None, None)

    def __init__(self, *args, **kwargs):
      super(Action, self).__init__(*args, **kwargs)
      option_strings = kwargs.get('option_strings')
      if option_strings:
        option_string = option_strings[0]
      else:
        option_string = None
      current = properties.VALUES.GetLatestInvocationValues().get(prop)
      properties.VALUES.SetInvocationValue(
          prop, current.value if current else None, option_string
      )

      if '_ARGCOMPLETE' in os.environ:
        self._orig_class = argparse._StoreAction  # pylint:disable=protected-access

    def __call__(self, parser, namespace, values, option_string=None):
      properties.VALUES.SetInvocationValue(prop, values, option_string)
      setattr(namespace, self.dest, values)

  return Action


def StoreBooleanProperty(prop: properties._Property) -> type[argparse.Action]:
  """Get an argparse action that stores a value in a Boolean property.

  Handles auto-generated --no-* inverted flags by inverting the value.

  Also stores the value in the namespace object, like the default action. The
  value is stored in the invocation stack, rather than persisted permanently.

  Args:
    prop: The property that should get the invocation value.

  Returns:
    An argparse action that routes the value correctly.
  """

  class Action(argparse.Action):
    """The action created for StoreBooleanProperty."""

    # store_property is referenced in calliope.parser_arguments.add_argument
    store_property = (prop, 'bool', None)

    def __init__(self, *args, **kwargs):
      kwargs = dict(kwargs)
      # Bool flags don't take any args.  There is one legacy one that needs to
      # so only do this if the flag doesn't specifically register nargs.
      if 'nargs' not in kwargs:
        kwargs['nargs'] = 0

      option_strings = kwargs.get('option_strings')
      if option_strings:
        option_string = option_strings[0]
      else:
        option_string = None
      if option_string and option_string.startswith('--no-'):
        self._inverted = True
        kwargs['nargs'] = 0
        kwargs['const'] = None
        kwargs['choices'] = None
      else:
        self._inverted = False
      super(Action, self).__init__(*args, **kwargs)

      current = properties.VALUES.GetLatestInvocationValues().get(prop)
      properties.VALUES.SetInvocationValue(
          prop, current.value if current else None, option_string
      )

      if '_ARGCOMPLETE' in os.environ:
        self._orig_class = argparse._StoreAction  # pylint:disable=protected-access

    def __call__(self, parser, namespace, values, option_string=None):
      if self._inverted:
        values = 'false'
      elif values == []:  # pylint: disable=g-explicit-bool-comparison, need exact [] equality test
        values = 'true'
      properties.VALUES.SetInvocationValue(prop, values, option_string)
      setattr(namespace, self.dest, values)

  return Action


def StoreConstProperty(
    prop: properties._Property,
    const: Any,
) -> type[argparse.Action]:
  """Get an argparse action that stores a constant in a property.

  Also stores the constant in the namespace object, like the store_true action.
  The const is stored in the invocation stack, rather than persisted
  permanently.

  Args:
    prop: The property that should get the invocation value.
    const: The constant that should be stored in the property.

  Returns:
    An argparse action that routes the value correctly.
  """

  class Action(argparse.Action):
    """The action created for StoreConstProperty."""

    # store_property is referenced in calliope.parser_arguments.add_argument
    store_property = (prop, 'value', const)

    def __init__(self, *args, **kwargs):
      kwargs = dict(kwargs)
      kwargs['nargs'] = 0
      super(Action, self).__init__(*args, **kwargs)

      if '_ARGCOMPLETE' in os.environ:
        self._orig_class = argparse._StoreConstAction  # pylint:disable=protected-access

    def __call__(self, parser, namespace, values, option_string=None):
      properties.VALUES.SetInvocationValue(prop, const, option_string)
      setattr(namespace, self.dest, const)

  return Action
