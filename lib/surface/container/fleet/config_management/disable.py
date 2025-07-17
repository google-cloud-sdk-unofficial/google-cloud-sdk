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

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet.features import base as features_base


@base.DefaultUniverseOnly
class Disable(features_base.DisableCommand):
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
  support_fleet_default = True

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
    super().Args(flag_group)
