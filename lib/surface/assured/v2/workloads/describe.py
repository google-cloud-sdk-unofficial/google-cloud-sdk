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
"""Command to describe an Assured Workloads V2 environment."""

from googlecloudsdk.api_lib.assured import endpoint_util
from googlecloudsdk.api_lib.assured import workloads as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.base import ReleaseTrack
from googlecloudsdk.command_lib.assured import flags

_DETAILED_HELP = {
    'DESCRIPTION': 'Describe an Assured Workloads V2 environment.',
    'EXAMPLES': (
        """\
        To describe an Assured Workloads V2 environment with ID 456 in organization 123 under us-central1:

          $ {command} 456 --organization=123 --location=us-central1
        """
    ),
}


@base.ReleaseTracks(ReleaseTrack.GA, ReleaseTrack.BETA, ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Describe(base.DescribeCommand):
  """Describe Assured Workloads V2 environment."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddDescribeWorkloadFlags(parser)

  def Run(self, args):
    """Run the describe command."""
    workload_resource = args.CONCEPTS.workload.Parse()
    region = workload_resource.Parent().Name()
    workload = workload_resource.RelativeName()
    with endpoint_util.AssuredWorkloadsEndpointOverridesFromRegion(
        release_track=self.ReleaseTrack(), region=region
    ):
      client = apis.WorkloadsClient(
          release_track=self.ReleaseTrack(), api_version='v2'
      )
      return client.DescribeV2(name=workload)
