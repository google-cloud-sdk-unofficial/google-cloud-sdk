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
"""Command for describing network location bindings."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.network_location_bindings import flags


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.PREVIEW)
class Describe(base.DescribeCommand):
  """Describe a Google Compute Engine network location binding."""

  detailed_help = {
      'brief': 'Describe a Google Compute Engine network location binding.',
      'DESCRIPTION': """\
      *{command}* displays all data associated with a regional network
      location binding, including its binding state, binding type, and the
      per-zone cluster bindings.
      """,
      'EXAMPLES': """\
      To describe a network location binding named `my-binding` in region
      `us-central1`, run:

        $ {command} my-binding --region=us-central1
      """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddNetworkLocationBindingResourceArg(parser, 'to describe')

  def Run(self, args):
    """Issue a NetworkLocationBindings GET request."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    binding_ref = args.CONCEPTS.name.Parse()

    request = client.messages.ComputeNetworkLocationBindingsGetRequest(
        project=binding_ref.project,
        region=binding_ref.region,
        networkLocationBinding=binding_ref.Name(),
    )

    return client.MakeRequests(
        [(client.apitools_client.networkLocationBindings, 'Get', request)]
    )[0]
