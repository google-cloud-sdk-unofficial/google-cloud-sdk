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
"""Implementation of list command for Feature Configs."""

from googlecloudsdk.api_lib.storage import feature_config_api
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class List(base.ListCommand):
  """List Cloud Storage Smart Storage Feature Configurations."""

  detailed_help = {
      'DESCRIPTION': (
          """
       *{command}* lists Cloud Storage Smart Storage Feature Configurations in a project.
      """
      ),
      'EXAMPLES': (
          """
       To list all Feature Configurations:

         $ {command}

       To list Feature Configurations with custom filtering:

         $ {command} --filter="auto_annotate_config"
      """
      ),
  }

  @classmethod
  def Args(cls, parser):
    super(List, cls).Args(parser)
    parser.display_info.AddFormat("""
        table(
            name.basename():label=FEATURE_CONFIG_ID,
            type:label=TYPE,
            description:label=DESCRIPTION,
            createTime:label=CREATE_TIME
        )
        """)

  def Run(self, args):
    client = feature_config_api.FeatureConfigApi()
    project = properties.VALUES.core.project.Get(required=True)
    parent = f'projects/{project}/locations/global'
    return client.list_feature_configs(parent, page_size=args.page_size)
