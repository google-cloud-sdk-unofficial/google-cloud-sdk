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

from googlecloudsdk.api_lib.storage import feature_config_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.core import properties


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
    client = feature_config_api.FeatureConfigApi()
    project = properties.VALUES.core.project.Get(required=True)
    name = (
        f'projects/{project}/locations/global/featureConfigs/{args.CONFIG_ID}'
    )

    description = args.description if args.IsSpecified('description') else None
    auto_annotate_models = (
        args.auto_annotate_models
        if args.IsSpecified('auto_annotate_models')
        else None
    )
    include_locations = (
        args.include_locations
        if args.IsSpecified('include_locations')
        else None
    )
    exclude_locations = (
        args.exclude_locations
        if args.IsSpecified('exclude_locations')
        else None
    )
    include_bucket_id_regexes = (
        args.include_bucket_id_regexes
        if args.IsSpecified('include_bucket_id_regexes')
        else None
    )
    exclude_bucket_id_regexes = (
        args.exclude_bucket_id_regexes
        if args.IsSpecified('exclude_bucket_id_regexes')
        else None
    )

    return client.update_feature_config(
        name=name,
        description=description,
        auto_annotate_models=auto_annotate_models,
        include_locations=include_locations,
        exclude_locations=exclude_locations,
        include_bucket_id_regexes=include_bucket_id_regexes,
        exclude_bucket_id_regexes=exclude_bucket_id_regexes,
    )
