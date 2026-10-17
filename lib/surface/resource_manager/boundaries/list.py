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
"""Command to list boundaries."""

from googlecloudsdk.api_lib.resource_manager import boundaries
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager.boundaries import flags


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class List(base.ListCommand):
  """List boundaries.

  `{command}` lists all boundaries under the specified organization or folder.

  ## EXAMPLES

  To list boundaries under an organization with ID `123456789012`, run:

    $ {command} --organization=123456789012

  To list boundaries under a folder with ID `456789012345`, run:

    $ {command} --folder=456789012345
  """

  @staticmethod
  def Args(parser):
    flags.AddParentFlagsToParser(parser)
    parser.display_info.AddFormat("""
        table(
          name.basename():label=ID,
          displayName:label=DISPLAY_NAME,
          managementProject:label=MANAGEMENT_PROJECT,
          resourceFilter.tagFilter.tagValue:label=TAG_VALUE,
          state:label=STATE
        )
    """)

  def Run(self, args):
    parent = flags.GetParentFromFlags(args)
    return boundaries.ListBoundaries(
        parent=parent,
        page_size=args.page_size,
    )
