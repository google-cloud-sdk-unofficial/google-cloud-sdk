# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to import an Attached cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import attached as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.attached import flags as attached_flags
from googlecloudsdk.command_lib.container.attached import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import command_util
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags

_EXAMPLES = """
To import the fleet membership of an attached cluster named ``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-cluster --location=us-west1 --platform-version=PLATFORM_VERSION --fleet-membership=FLEET_MEMBERSHIP --distribution=DISTRIBUTION
"""


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Import(base.Command):
  """Import fleet membership for an Attached cluster."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    resource_args.AddLocationResourceArg(parser, 'to import attached cluster.')
    resource_args.AddFleetMembershipResourceArg(parser)

    attached_flags.AddPlatformVersion(parser)
    attached_flags.AddDistribution(parser, required=True)

    flags.AddValidateOnly(parser, 'cluster to import')

    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Runs the generate-install-manifest command."""
    location_ref = args.CONCEPTS.location.Parse()
    fleet_membership_ref = args.CONCEPTS.fleet_membership.Parse()
    with endpoint_util.GkemulticloudEndpointOverride(location_ref.locationsId):
      cluster_client = api_util.ClustersClient()
      message = command_util.ClusterMessage(
          fleet_membership_ref.RelativeName(),
          action='Importing',
          kind=constants.ATTACHED)
      return command_util.Import(
          location_ref=location_ref,
          resource_client=cluster_client,
          fleet_membership_ref=fleet_membership_ref,
          args=args,
          message=message,
          kind=constants.ATTACHED_CLUSTER_KIND)
