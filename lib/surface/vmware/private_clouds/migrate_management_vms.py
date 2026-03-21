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
"""'vmware private-clouds migrate-management-vms' command."""

from googlecloudsdk.api_lib.vmware.privateclouds import PrivateCloudsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': """
          Migrate the management VMs of a private cloud from the current management cluster to a workload cluster. Post this migration, the provided workload cluster becomes the management cluster for the private cloud.
      """,
    'EXAMPLES': """
          To migrate management VMs of the private cloud `my-private-cloud` from the management cluster to the workload cluster `my-cluster`, run:

            $ {command} my-private-cloud --cluster=my-cluster --location=us-west1-a --project=my-project

          Or:

            $ {command} my-private-cloud --cluster=my-cluster

          In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
      """,
}


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class MigrateManagementVms(base.Command):
  """Migrate the management VMs of a private cloud to a workload cluster."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser, positional=True)
    parser.add_argument(
        '--cluster',
        required=True,
        help='The ID of the cluster to migrate the management VMs to.',
    )
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)

  def Run(self, args):
    privatecloud = args.CONCEPTS.private_cloud.Parse()
    client = PrivateCloudsClient()
    is_async = args.async_
    operation = client.MigrateManagementVms(privatecloud, args.cluster)
    if is_async:
      log.UpdatedResource(
          operation.name, kind='private cloud management VMs', is_async=True
      )
      return

    message_string = (
        'Waiting for private cloud [{}] management VMs to be migrated'
    )
    client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=(message_string.format(privatecloud.RelativeName())),
        has_result=False,
    )

    log.UpdatedResource(privatecloud.RelativeName(), kind='private cloud')
    return
