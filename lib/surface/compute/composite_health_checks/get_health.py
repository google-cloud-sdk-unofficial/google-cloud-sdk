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
"""Command for getting health of a composite health check."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.composite_health_checks import flags


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class GetHealth(base.DescribeCommand):
  """Get health status of a composite health check."""

  detailed_help = {
      'EXAMPLES': (
          """
      To get health of a composite health check, run:

        $ {command} COMPOSITE_HEALTH_CHECK --region=REGION
      """
      ),
  }

  @staticmethod
  def Args(parser):
    flags.CompositeHealthCheckArgument().AddArgument(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    composite_health_check_ref = (
        flags.CompositeHealthCheckArgument().ResolveAsResource(
            args, holder.resources
        )
    )
    request = (
        client.messages.ComputeRegionCompositeHealthChecksGetHealthRequest(
            compositeHealthCheck=composite_health_check_ref.Name(),
            project=composite_health_check_ref.project,
            region=composite_health_check_ref.region,
        )
    )

    response = client.apitools_client.regionCompositeHealthChecks.GetHealth(
        request
    )
    return [response]
