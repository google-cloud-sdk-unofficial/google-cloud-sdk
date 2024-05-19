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
from googlecloudsdk.command_lib.container.fleet.packages import utils
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To view Rollout ``20240318'' for ``cert-manager-app'' in ``us-central1'', run:

          $ {command} 20240318 --fleet-package=cert-manager-app --location=us-central1
        """,
}

_FULL_MESSAGES_FORMAT = """table(release.segment(5):label=RESOURCE_BUNDLE,
                    info.rolloutStrategyInfo.rollingStrategyInfo.clusters.membership.basename():label=CLUSTER,
                    info.state:label=ROLLOUT_STATE,
                    release.basename():label=RELEASE,
                    info.rolloutStrategyInfo.rollingStrategyInfo.clusters.current.version:label=CURRENT_VERSION,
                    info.rolloutStrategyInfo.rollingStrategyInfo.clusters.current.syncState:label=CURRENT_STATE,
                    info.rolloutStrategyInfo.rollingStrategyInfo.clusters.desired.version:label=DESIRED_VERSION,
                    info.rolloutStrategyInfo.rollingStrategyInfo.clusters.desired.syncState:label=DESIRED_STATE,
                    info.rolloutStrategyInfo.rollingStrategyInfo.clusters.startTime:label=START_TIME,
                    info.rolloutStrategyInfo.rollingStrategyInfo.clusters.endTime:label=END_TIME,
                    all_messages():label=MESSAGES)"""

_FORMAT_TRUNCATED_MESSAGES = """table(release.segment(5):label=RESOURCE_BUNDLE,
                    info.rolloutStrategyInfo.rollingStrategyInfo.clusters.membership.basename():label=CLUSTER,
                    info.state:label=ROLLOUT_STATE,
                    release.basename():label=RELEASE,
                    info.rolloutStrategyInfo.rollingStrategyInfo.clusters.current.version:label=CURRENT_VERSION,
                    info.rolloutStrategyInfo.rollingStrategyInfo.clusters.current.syncState:label=CURRENT_STATE,
                    info.rolloutStrategyInfo.rollingStrategyInfo.clusters.desired.version:label=DESIRED_VERSION,
                    info.rolloutStrategyInfo.rollingStrategyInfo.clusters.desired.syncState:label=DESIRED_STATE,
                    info.rolloutStrategyInfo.rollingStrategyInfo.clusters.startTime:label=START_TIME,
                    info.rolloutStrategyInfo.rollingStrategyInfo.clusters.endTime:label=END_TIME,
                    trim_message():label=MESSAGE)"""


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe Rollout resource."""

  detailed_help = _DETAILED_HELP
  show_less = False

  def Epilog(self, resources_were_displayed):
    if resources_were_displayed and self.show_less:
      log.status.Print('\nRollout messages too long? Try --less.')

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(_FULL_MESSAGES_FORMAT)
    parser.display_info.AddTransforms(
        {'all_messages': utils.TransformAllMessages}
    )
    parser.display_info.AddTransforms(
        {'trim_message': utils.TransformTrimMessage}
    )
    flags.AddNameFlag(parser)
    flags.AddFleetPackageFlag(parser)
    flags.AddLocationFlag(parser)
    flags.AddLessFlag(parser)

  def Run(self, args):
    """Run the describe command."""
    client = apis.RolloutsClient()
    if args.less:
      args.format = _FORMAT_TRUNCATED_MESSAGES

    output = client.Describe(
        fleet_package=args.fleet_package,
        project=flags.GetProject(args),
        location=flags.GetLocation(args),
        rollout=args.name,
    )
    if output.info and output.info.rolloutStrategyInfo:
      if output.info.rolloutStrategyInfo.rollingStrategyInfo:
        args.flatten = [
            'info.rolloutStrategyInfo.rollingStrategyInfo.clusters[]'
        ]
      if output.info.rolloutStrategyInfo.allAtOnceStrategyInfo:
        args.flatten = [
            'info.rolloutStrategyInfo.allAtOnceStrategyInfo.clusters[]'
        ]
    if output.info and output.info.message:
      if not args.less:
        self.show_less = True
    return output
