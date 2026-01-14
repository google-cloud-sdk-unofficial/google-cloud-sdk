# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""'vmware datastores create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware import datastores
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DatastoresClient = datastores.DatastoresClient
DETAILED_HELP = {
    'DESCRIPTION': """
          Create a datastore. Datastore creation is considered finished when the datastore is in ACTIVE state. Check the progress of a datastore using `{parent_command} list`.
        """,
    'EXAMPLES': """
          To create a datastore named `my-datastore` in `us-west2-a` connected to filestore instance `projects/my-project/locations/us-west2-a/instances/my-filestore-instance`, run:

          $ {command} my-datastore --location=us-west2-a --project=my-project --filestore=projects/my-project/locations/us-west2-a/instances/my-filestore-instance

          Or:

          $ {command} my-datastore --filestore=projects/my-project/locations/us-west2-a/instances/my-filestore-instance

          Or:

          $ {command} my-datastore --netapp=projects/my-project/locations/us-west2-a/volumes/my-netapp-volume

          Or:

          $ {command} my-datastore --third-party-nfs-network=my-network --third-party-nfs-file-share=my-fileshare --third-party-nfs-servers=10.0.0.1,10.0.0.2 --location=us-west2-a --project=my-project

          In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.DefaultUniverseOnly
class Create(base.CreateCommand):
  """Create a datastore."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddDatastoreArgToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--description',
        help="""\
        Text describing the datastore.
        """,
    )
    datastore_type_group = parser.add_group(
        mutex=True,
        required=True,
    )
    datastore_type_group.add_argument(
        '--netapp',
        help="""\
        Google NetApp volume to be used as datastore.
        """,
    )
    datastore_type_group.add_argument(
        '--filestore',
        help="""\
        Google Filestore instance to be used as datastore.
        """,
    )
    third_party_nfs_group = datastore_type_group.add_group()
    third_party_nfs_group.add_argument(
        '--third-party-nfs-network',
        required=True,
        help="""\
        Network name of NFS's VPC.
        """,
    )
    third_party_nfs_group.add_argument(
        '--third-party-nfs-file-share',
        required=True,
        help="""\
        Mount folder name of NFS.
        """,
    )
    third_party_nfs_group.add_argument(
        '--third-party-nfs-servers',
        required=True,
        help="""\
        Comma-separated list of server IP addresses of the NFS file service.
        """,
        type=arg_parsers.ArgList(min_length=1),
        metavar='SERVER',
    )

  def Run(self, args):
    datastore = args.CONCEPTS.datastore.Parse()
    client = DatastoresClient()
    is_async = args.async_
    operation = client.Create(
        datastore,
        description=args.description,
        netapp_volume=args.netapp,
        filestore_instance=args.filestore,
        third_party_nfs_network=args.third_party_nfs_network,
        third_party_nfs_file_share=args.third_party_nfs_file_share,
        third_party_nfs_servers=args.third_party_nfs_servers,
    )
    if is_async:
      log.CreatedResource(operation.name, kind='datastore', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for datastore [{}] to be created'.format(
            datastore.RelativeName()
        ),
    )
    log.CreatedResource(datastore.RelativeName(), kind='datastore')
    return resource
