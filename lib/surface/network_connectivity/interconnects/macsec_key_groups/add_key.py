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
"""Command for adding a key to an Interconnect MACsec key group."""

from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_connectivity import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import times


@base.Hidden
@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class AddKey(base.Command):
  """Add a MACsec key to an Interconnect MACsec key group."""

  @staticmethod
  def Args(parser):
    flags.AddMacsecKeyGroupResourceArg(parser, 'to add key to')
    parser.add_argument(
        '--key-name',
        required=True,
        help='Name of the MACsec key to add.',
    )
    parser.add_argument(
        '--start-time',
        required=True,
        type=arg_parsers.Datetime.Parse,
        help='ISO 8601 timestamp of when this key takes effect.',
    )
    parser.add_argument(
        '--ckn',
        required=True,
        help='MACsec connectivity association key name (CKN).',
    )
    cak_group = parser.add_mutually_exclusive_group(required=True)
    cak_group.add_argument(
        '--cak',
        help='MACsec connectivity association key (CAK).',
    )
    cak_group.add_argument(
        '--cak-file',
        type=arg_parsers.FileContents(),
        help=(
            'Path to file containing the MACsec connectivity association key'
            ' (CAK).'
        ),
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    client = networkconnectivity_util.GetClientInstance(self.ReleaseTrack())
    messages = networkconnectivity_util.GetMessagesModule(self.ReleaseTrack())

    key_group_ref = args.CONCEPTS.macsec_key_group.Parse()

    key_name = args.key_name
    cak = (args.cak or args.cak_file).strip()
    if args.start_time.microsecond:
      start_time = times.FormatDateTime(
          args.start_time, '%Y-%m-%dT%H:%M:%S.%6f%Ez', tzinfo=times.UTC
      )
    else:
      start_time = times.FormatDateTime(
          args.start_time, '%Y-%m-%dT%H:%M:%S%Ez', tzinfo=times.UTC
      )
    macsec_key = messages.GoogleCloudNetworkconnectivityV1betaMacsecKey(
        name=key_name,
        startTime=start_time,
        ckn=args.ckn.strip(),
        cak=cak,
    )

    key_group = messages.GoogleCloudNetworkconnectivityV1betaInterconnectKeyGroup(
        keys=messages.GoogleCloudNetworkconnectivityV1betaInterconnectKeyGroup.KeysValue(
            additionalProperties=[
                messages.GoogleCloudNetworkconnectivityV1betaInterconnectKeyGroup.KeysValue.AdditionalProperty(
                    key=key_name, value=macsec_key
                )
            ]
        )
    )

    update_mask = f'keys.{key_name}'

    request = messages.NetworkconnectivityProjectsLocationsInterconnectKeyGroupsPatchRequest(
        name=key_group_ref.RelativeName(),
        googleCloudNetworkconnectivityV1betaInterconnectKeyGroup=key_group,
        updateMask=update_mask,
    )

    op_ref = client.projects_locations_interconnectKeyGroups.Patch(request)

    log.status.Print(f'Add key request issued for: [{key_group_ref.Name()}]')

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
        f'Waiting for operation [{op_ref.name}] to complete',
    )
