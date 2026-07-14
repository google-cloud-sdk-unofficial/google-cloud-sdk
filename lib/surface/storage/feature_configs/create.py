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

"""Implementation of create command for Feature Configs."""

from googlecloudsdk.api_lib.storage import feature_config_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.core import properties


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Create(base.Command):
  """Create a new Feature Config."""

  hints = base.CommandHint(read_only=False)

  detailed_help = {
      'DESCRIPTION': (
          """
       Create a new Feature Config.
      """
      ),
      'EXAMPLES': (
          """
      To create a Feature Config with config name "my_config" and auto-annotate model "face-detector":

         $ {command} my_config --auto-annotate-models=face-detector
      """
      ),
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'CONFIG_ID',
        help='The ID of the feature configuration to create.',
    )
    flags.add_feature_config_description_flag(parser)
    flags.add_feature_config_filter_flags(parser)
    models_group = parser.add_mutually_exclusive_group(required=True)
    flags.add_feature_config_auto_annotate_models_flag(models_group)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    client = feature_config_api.FeatureConfigApi()
    project = properties.VALUES.core.project.Get(required=True)
    parent = f'projects/{project}/locations/global'

    return client.create_feature_config(
        parent=parent,
        feature_config_id=args.CONFIG_ID,
        description=args.description,
        auto_annotate_models=args.auto_annotate_models,
        include_locations=args.include_locations,
        exclude_locations=args.exclude_locations,
        include_bucket_id_regexes=args.include_bucket_id_regexes,
        exclude_bucket_id_regexes=args.exclude_bucket_id_regexes,
    )
