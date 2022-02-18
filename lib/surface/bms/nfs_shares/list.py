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
"""'Bare Metal Solution NFS shares list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector


DETAILED_HELP = {
    'DESCRIPTION':
        """
          List Bare Metal Solution NFS shares in a project.
        """,
    'EXAMPLES':
        """
          To list NFS shares within the project in the region ``us-central1'', run:

            $ {command} --region=us-central1

          Or:

          To list all NFS shares in the project, run:

            $ {command}
    """,
}


# TODO(b/218692770): Unhide class when NFS APIs are ready in prod.
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Bare Metal Solution NFS shares in a project."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    # Remove unsupported default List flags.
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.SORT_BY_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)

    flags.AddRegionArgToParser(parser)
    # The default format picks out the components of the relative name:
    # given projects/myproject/locations/us-central1/nfs-shares/my-test
    # it takes -1 (my-test), -3 (us-central1), and -5 (myproject).
    parser.display_info.AddFormat(
        'table(name.segment(-1):label=NAME,nfsShareId:label=ID,'
        'name.segment(-5):label=PROJECT,name.segment(-3):label=REGION,'
        'volume.segment(-1):label=VOLUME_NAME,state,'
        'allowedClients:label=ALLOWED_CLIENTS)')

  def Run(self, args):
    region = args.CONCEPTS.region.Parse()
    client = BmsClient()
    if region is None:
      project = properties.VALUES.core.project.Get(required=True)
      return (self.synthesizedNfsShare(nfs_share)
              for nfs_share in client.AggregateListNfsShares(
                  project, limit=args.limit))
    return (self.synthesizedNfsShare(nfs_share)
            for nfs_share in client.ListNfsShares(region, limit=args.limit))

  def synthesizedNfsShare(self, nfs):
    """Returns a synthesized NFS share resource.

    Synthesized NFS shares has the allowedClients field transformed
    to a more compact format that allows it to be displayed in the list
    stdout table.

    Args:
      nfs: protorpc.messages.Message, The BMS NFS share.

    Returns:
      Synthesized NFS share resource.

    """
    out = resource_projector.MakeSerializable(nfs)
    out['allowedClients'] = []
    for nfs_client in nfs.allowedClients:
      # Name is the last element in path.
      network_name = nfs_client.network.split('/')[-1]
      nfs_client_summary = {
          'networkName': network_name,
          'allowedCidr': nfs_client.allowedClientsCidr,
          'shareIp': nfs_client.shareIp,
      }
      out['allowedClients'].append(nfs_client_summary)
    # We dump jsons here because when we use the built-in serialization, it
    # sometimes adds a 'u' character before the strings and the tests break.
    out['allowedClients'] = json.dumps(out['allowedClients'], sort_keys=True)
    return out

List.detailed_help = DETAILED_HELP
