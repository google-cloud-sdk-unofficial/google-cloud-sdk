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
"""Command for removing a key from an Interconnect MACsec key group."""

from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_connectivity import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@base.Hidden
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class RemoveKey(base.Command):
  """Remove a MACsec key from an Interconnect MACsec key group."""

  @staticmethod
  def Args(parser):
    flags.AddMacsecKeyGroupResourceArg(parser, 'to remove key from')
    parser.add_argument(
        '--key-name',
        required=True,
        help='Name of the MACsec key to remove.',
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    client = networkconnectivity_util.GetClientInstance(self.ReleaseTrack())
    messages = networkconnectivity_util.GetMessagesModule(self.ReleaseTrack())

    key_group_ref = args.CONCEPTS.macsec_key_group.Parse()

    key_name = args.key_name
    key_group = (
        messages.GoogleCloudNetworkconnectivityV1betaInterconnectKeyGroup()
    )

    update_mask = f'keys.{key_name}'

    request = messages.NetworkconnectivityProjectsLocationsInterconnectKeyGroupsPatchRequest(
        name=key_group_ref.RelativeName(),
        googleCloudNetworkconnectivityV1betaInterconnectKeyGroup=key_group,
        updateMask=update_mask,
    )

    op_ref = client.projects_locations_interconnectKeyGroups.Patch(request)

    log.status.Print(
        'Remove key request issued for: [{}]'.format(key_group_ref.Name())
    )

    if args.async_:
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='networkconnectivity.projects.locations.operations',
        api_version=networkconnectivity_util.VERSION_MAP[self.ReleaseTrack()],
    )
    poller = waiter.CloudOperationPoller(
        client.projects_locations_interconnectKeyGroups,
        client.projects_locations_operations,
    )
    return waiter.WaitFor(
        poller,
        op_resource,
        'Waiting for operation [{}] to complete'.format(op_ref.name),
    )


RemoveKey.detailed_help = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': (
        """\
        To remove a MACsec key named 'key-1' from a MACsec key group named 'my-key-group' in region 'us-central1', run:

          $ {command} my-key-group --region=us-central1 --key-name=key-1
        """
    ),
}
