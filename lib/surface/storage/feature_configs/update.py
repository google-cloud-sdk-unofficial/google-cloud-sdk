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

"""Implementation of update command for Feature Configs."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Update(base.Command):
  """Update a Feature Config."""

  hints = base.CommandHint(read_only=False)

  detailed_help = {
      'DESCRIPTION': (
          """
       Update an existing Feature Config.
      """
      ),
      'EXAMPLES': (
          """
      To update a Feature Config named "my_config" to clear include locations:

         $ {command} my_config --include-locations=""
      """
      ),
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'CONFIG_ID',
        help='The ID of the feature configuration to update.',
    )
    flags.add_feature_config_description_flag(parser)
    flags.add_feature_config_filter_flags(parser)
    flags.add_feature_config_auto_annotate_models_flag(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    del self, args  # Unused.
    raise NotImplementedError(
        'The feature-configs surface is not yet implemented.'
    )
