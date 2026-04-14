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
"""Command for getting health of a health source."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.health_sources import flags


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class GetHealth(base.DescribeCommand):
  """Get health status of a health source."""

  detailed_help = {
      'EXAMPLES': (
          """
      To get health status of a single health source, run:

        $ {command} HEALTH_SOURCE --region=REGION
      """
      ),
  }

  @staticmethod
  def Args(parser):
    flags.HealthSourceArgument().AddArgument(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    health_source_ref = flags.HealthSourceArgument().ResolveAsResource(
        args, holder.resources
    )
    request = client.messages.ComputeRegionHealthSourcesGetHealthRequest(
        healthSource=health_source_ref.Name(),
        project=health_source_ref.project,
        region=health_source_ref.region,
    )

    response = client.apitools_client.regionHealthSources.GetHealth(request)
    return [response]
