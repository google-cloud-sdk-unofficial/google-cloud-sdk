# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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

"""List command for Colab Enterprise Schedules."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.colab_enterprise import util
from googlecloudsdk.api_lib.notebook_executor import schedules as schedules_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.notebook_executor import flags


_DETAILED_HELP = {
    'DESCRIPTION': """
        List your project's Colab Enterprise notebook execution schedules in a given region.
    """,
    'EXAMPLES': """
        To list your schedules in region `us-central1`, run:

        $ {command} --region=us-central1
    """,
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List your Colab Enterprise notebook execution schedules."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddListSchedulesFlags(parser)
    parser.display_info.AddFormat("""
        table(name.segment(-1):label=ID,
        displayName,
        state,
        cron,
        nextRunTime)
    """)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    release_track = self.ReleaseTrack()
    messages = util.GetMessages(self.ReleaseTrack())
    region_ref = args.CONCEPTS.region.Parse()
    region = region_ref.AsDict()['locationsId']
    # Override to regionalize domain as used by the AIPlatform API.
    with endpoint_util.AiplatformEndpointOverrides(
        version='BETA', region=region
    ):
      api_client = util.GetClient(release_track)
      schedules_service = (
          api_client.projects_locations_schedules
      )
      return list_pager.YieldFromList(
          service=schedules_service,
          request=schedules_util.CreateScheduleListRequest(
              args, messages
          ),
          field='schedules',
          limit=args.limit,
          batch_size_attribute='pageSize',
          batch_size=args.page_size,
      )

List.detailed_help = _DETAILED_HELP
