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

"""Implementation of describe command for Feature Configs."""

from googlecloudsdk.api_lib.storage import feature_config_api
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Describe(base.DescribeCommand):
  """Describe a Feature Config."""

  detailed_help = {
      'DESCRIPTION': (
          """
       Describe a Feature Config.
      """
      ),
      'EXAMPLES': (
          """
      To describe a Feature Config named "my_config":

         $ {command} my_config
      """
      ),
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'CONFIG_ID',
        help='The ID of the feature configuration to describe.',
    )

  def Run(self, args):
    client = feature_config_api.FeatureConfigApi()
    project = properties.VALUES.core.project.Get(required=True)
    name = (
        f'projects/{project}/locations/global/featureConfigs/{args.CONFIG_ID}'
    )
    return client.get_feature_config(name)
