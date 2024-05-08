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
"""Command to describe Rollout in a project."""

from googlecloudsdk.api_lib.container.fleet.packages import rollouts as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet.packages import flags

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To view Rollout ``20240318'' for ``cert-manager-app'' in ``us-central1'', run:

          $ {command} 20240318 --fleet-package=cert-manager-app --location=us-central1
        """,
}

_FORMAT = """table(release.segment(5):label=RESOURCE_BUNDLE,
                    info.clusterInfo.membership.basename():label=CLUSTER,
                    info.clusterInfo.currentResourceBundleInfo.version:label=CURRENT_VERSION,
                    info.clusterInfo.currentResourceBundleInfo.state:label=CURRENT_STATE,
                    info.clusterInfo.desiredResourceBundleInfo.version:label=DESIRED_VERSION,
                    info.clusterInfo.desiredResourceBundleInfo.state:label=DESIRED_STATE,
                    info.clusterInfo.currentResourceBundleInfo.reconciliationStartTime:label=START_TIME,
                    info.clusterInfo.currentResourceBundleInfo.reconciliationEndTime:label=END_TIME)"""


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe Rollout resource."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    parser.display_info.AddFlatten(['info.clusterInfo[]'])
    parser.display_info.AddFormat(_FORMAT)
    flags.AddNameFlag(parser)
    flags.AddFleetPackageFlag(parser)
    flags.AddLocationFlag(parser)

  def Run(self, args):
    """Run the describe command."""
    client = apis.RolloutsClient()
    return client.Describe(
        fleet_package=args.fleet_package,
        project=flags.GetProject(args),
        location=flags.GetLocation(args),
        rollout=args.name,
    )
