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
"""Command to list Assured Workloads V2 environments."""

from googlecloudsdk.api_lib.assured import endpoint_util
from googlecloudsdk.api_lib.assured import message_util
from googlecloudsdk.api_lib.assured import workloads as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.base import ReleaseTrack
from googlecloudsdk.command_lib.assured import flags

_DETAILED_HELP = {
    'DESCRIPTION': (
        'List Assured Workloads V2 environments that belong to a given parent'
        ' organization.'
    ),
    'EXAMPLES': (
        """\
        To list all Assured Workloads V2 environments in organization 123 under location us-central1:

          $ {command} --organization=123 --location=us-central1
        """
    ),
}

_FORMAT_V2 = """
    table(
        name.segment(-1):label=ID,
        targetResourceDisplayName:label=DISPLAY_NAME,
        computedTargetResource:label=TARGET_RESOURCE,
        framework.framework:label=FRAMEWORK,
        state:label=STATE,
        createTime:label=CREATE_TIME
    )
"""


@base.ReleaseTracks(ReleaseTrack.GA, ReleaseTrack.BETA, ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class List(base.ListCommand):
  """List Assured Workloads V2 environments that belong to a given parent organization."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddListWorkloadsFlags(parser)
    parser.display_info.AddFormat(_FORMAT_V2)

  def Run(self, args):
    """Run the list command."""
    server_filter = args.filter
    args.filter = None  # Prevent Calliope from applying client-side post-filter
    with endpoint_util.AssuredWorkloadsEndpointOverridesFromRegion(
        release_track=self.ReleaseTrack(), region=args.location
    ):
      client = apis.WorkloadsClient(
          release_track=self.ReleaseTrack(), api_version='v2'
      )
      return client.ListV2(
          parent=message_util.CreateAssuredParent(
              args.organization, args.location
          ),
          limit=args.limit,
          page_size=args.page_size,
          filter_str=server_filter,
      )
