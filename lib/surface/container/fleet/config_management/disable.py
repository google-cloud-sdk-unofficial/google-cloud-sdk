# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""The command to disable Config Management Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.core import exceptions
import six


class Disable(base.DisableCommand, base.UpdateCommand):
  """Disable Config Management feature.

  Disable the Config Management feature in a fleet. Disable the feature entirely
  or only disable [fleet-default membership configuration
  ](https://cloud.google.com/kubernetes-engine/fleet-management/docs/manage-features)
  for the feature.

  ## EXAMPLES

  To disable the Config Management feature entirely, run:

    $ {command}

  To disable only fleet-default membership configuration for the feature,
  run:

    $ {command} --fleet-default-member-config
  """

  feature_name = 'configmanagement'

  @classmethod
  def Args(cls, parser):
    """Adds flags to the command.

    Adds --force and --fleet-default-member-config as mutually exclusive flags
    to the parser for this command.

    Args:
      parser: googlecloudsdk.calliope.parser_arguments.ArgumentInterceptor,
        Argument parser to add flags to.
    """
    flag_group = parser.add_group(mutex=True)
    base.DisableCommand.Args(flag_group)
    flag_group.add_argument(
        '--fleet-default-member-config',
        action='store_true',
        help=(
            'Disable [fleet-default membership configuration]('
            'https://cloud.google.com/kubernetes-engine/fleet-management/docs/manage-features)'
            ' without disabling the feature.'
            ' Does not change existing membership configurations.'
            ' Exits silently if the feature is not enabled.'
        ),
    )

  def Run(self, args):
    """Executes command logic.

    Disables parts of or the entire feature specified by args.

    Args:
      args: Flags, either --force or --fleet-default-member-config, specified in
        the call. The value associated with each flag is stored on an args field
        that is named after the flag with dashes replaced with underscores.
    """
    if args.fleet_default_member_config:
      # A return statement would expose updated feature to user.
      _ = self._clear_fleet_default()
    else:
      # Never returns anything.
      self.Disable(args.force)

  def _clear_fleet_default(self):
    """Unsets the fleet-default config for the Config Management feature.

    Returns:
      The feature with the fleet-default config cleared, if the feature exists.
      Otherwise, None, without raising an error.
    """
    mask = ['fleet_default_member_config']
    # Feature cannot be empty on update, which would be the case without the
    # placeholder name field when we try to clear the fleet default config.
    # The placeholder name field must not be in the mask, lest we actually
    # change the feature name.
    # TODO(b/302390572): Replace with better solution if found.
    patch = self.messages.Feature(name='placeholder')
    try:
      return self.Update(mask, patch)
    except exceptions.Error as e:
      # Do not error or log if feature does not exist.
      if six.text_type(e) != six.text_type(self.FeatureNotEnabledError()):
        raise e
