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
"""List command for the Resource Manager - CapabilityConfigs CLI."""

from googlecloudsdk.api_lib.resource_manager import capability_configs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager.capability_configs import flags


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class List(base.ListCommand):
  r"""List CapabilityConfigs that are direct children of a parent resource.

  Lists all CapabilityConfigs under an organization, folder, or project.

  ## EXAMPLES

  To list CapabilityConfigs under organization `123456789`:

        $ {command} --organization=123456789

  To list CapabilityConfigs under folder `456789012`:

        $ {command} --folder=456789012

  To list CapabilityConfigs under project `my-project`:

        $ {command} --project=my-project
  """

  @staticmethod
  def Args(parser):
    flags.AddParentFlagsToParser(
        parser,
        'to list capability configs for',
    )
    base.PAGE_SIZE_FLAG.SetDefault(parser, 100)
    base.LIMIT_FLAG.SetDefault(parser, 500)
    parser.display_info.AddFormat("""
        table(
          name.basename():label=ID,
          displayName:label=DISPLAY_NAME,
          managementProject:label=MANAGEMENT_PROJECT,
          types.list():label=TYPES,
          state:label=STATE
        )
    """)

  def Run(self, args):
    parent = flags.GetParentFromArgs(args)
    return capability_configs.List(
        parent=parent,
        page_size=args.page_size,
        limit=args.limit,
    )
