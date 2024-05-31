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
"""Command to list all Rollouts of a Fleet Package."""

from googlecloudsdk.api_lib.container.fleet.packages import rollouts as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet.packages import flags
from googlecloudsdk.command_lib.container.fleet.packages import utils

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To list all Rollouts for Fleet Package `cert-manager-app` in `us-central1`, run:

          $ {command} --fleet-package=cert-manager-app --location=us-central1
        """,
}

# For more formatting options see:
# http://cloud/sdk/gcloud/reference/topic/formats
_FORMAT = """table(name.basename():label=ROLLOUT,
                   release.basename():label=RELEASE,
                   info.startTime:label=START_TIME:sort=1:reverse,
                   info.endTime:label=END_TIME,
                   info.state:label=STATE,
                   info.message:label=MESSAGE)"""

_FORMAT_TRUNCATED_MESSAGES = """table(name.basename():label=ROLLOUT,
                                      release.basename():label=RELEASE,
                                      info.startTime:label=START_TIME:sort=1:reverse,
                                      info.endTime:label=END_TIME,
                                      info.state:label=STATE,
                                      trim_message():label=MESSAGE)"""


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Rollouts of a Fleet Package."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddUriFunc(apis.GetRolloutURI)
    parser.display_info.AddTransforms(
        {'trim_message': utils.TransformTrimMessage}
    )
    flags.AddLocationFlag(parser)
    flags.AddFleetPackageFlag(parser)
    flags.AddLessFlag(parser)

  def Run(self, args):
    """Run the list command."""
    client = apis.RolloutsClient()
    if args.less:
      args.format = _FORMAT_TRUNCATED_MESSAGES

    return client.List(
        project=flags.GetProject(args),
        location=flags.GetLocation(args),
        fleet_package=args.fleet_package,
        limit=args.limit,
        page_size=args.page_size,
    )
