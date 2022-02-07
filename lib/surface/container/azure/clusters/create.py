# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command to create an Anthos cluster on Azure."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.azure import util as azure_api_util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container.azure import resource_args
from googlecloudsdk.command_lib.container.azure import util as command_util
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.command_lib.container.gkemulticloud import operations
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


# Command needs to be in one line for the docgen tool to format properly.
_EXAMPLES = """
To create a cluster named ``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-cluster --location=us-west1 --azure-region=AZURE_REGION --cluster-version=CLUSTER_VERSION --client=CLIENT --pod-address-cidr-blocks=POD_ADDRESS_CIDR_BLOCKS --resource-group-id=RESOURCE_GROUP_ID --ssh-public-key=SSH_PUBLIC_KEY --subnet-id=SUBNET_ID --vnet-id=VNET_ID
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create an Anthos cluster on Azure."""

  detailed_help = {"EXAMPLES": _EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddAzureClusterAndClientResourceArgs(parser)

    parser.add_argument(
        "--azure-region",
        action=actions.StoreProperty(properties.VALUES.azure.azure_region),
        required=True,
        help=("Azure location to deploy the cluster. "
              "Refer to your Azure subscription for available locations."))
    parser.add_argument(
        "--resource-group-id",
        required=True,
        help=("ID of the Azure Resource Group "
              "to associate the cluster with."))
    parser.add_argument(
        "--vnet-id",
        required=True,
        help=("ID of the Azure Virtual Network "
              "to associate with the cluster."))
    parser.add_argument(
        "--service-load-balancer-subnet-id",
        help=("ARM ID of the subnet where Kubernetes private service type "
              "load balancers are deployed, when the Service lacks a subnet "
              "annotation."))
    parser.add_argument(
        "--endpoint-subnet-id",
        help=("ARM ID of the subnet where the control plane load balancer "
              "is deployed. When unspecified, it defaults to the control "
              "plane subnet ID."))
    flags.AddPodAddressCidrBlocks(parser)
    flags.AddServiceAddressCidrBlocks(parser)
    flags.AddClusterVersion(parser)
    flags.AddSubnetID(parser, "the cluster control plane", required=False)
    flags.AddVMSize(parser)
    flags.AddSSHPublicKey(parser)
    flags.AddRootVolumeSize(parser)
    flags.AddMainVolumeSize(parser)
    flags.AddReplicaPlacements(parser)
    flags.AddTags(parser, "cluster")
    flags.AddValidateOnly(parser, "creation of the cluster")
    flags.AddDatabaseEncryption(parser)
    flags.AddConfigEncryption(parser)
    flags.AddProxyConfig(parser)
    flags.AddFleetProject(parser)
    flags.AddAdminUsers(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddFormat(command_util.CLUSTERS_FORMAT)

  def Run(self, args):
    """Runs the create command."""

    azure_region = getattr(args, "azure_region", None)
    if not azure_region:
      try:
        azure_region = properties.VALUES.azure.azure_region.GetOrFail()
      except properties.RequiredPropertyError:
        raise exceptions.RequiredArgumentException("--azure-region",
                                                   "Must be specified.")

    resource_group_id = args.resource_group_id
    vnet_id = args.vnet_id
    pod_address_cidr_blocks = args.pod_address_cidr_blocks
    service_address_cidr_blocks = args. service_address_cidr_blocks
    replica_placements = args.replica_placements
    cluster_version = flags.GetClusterVersion(args)
    subnet_id = flags.GetSubnetID(args)
    vm_size = flags.GetVMSize(args)
    ssh_public_key = flags.GetSSHPublicKey(args)
    proxy_resource_group_id = args.proxy_resource_group_id
    proxy_secret_id = args.proxy_secret_id
    root_volume_size = flags.GetRootVolumeSize(args)
    main_volume_size = flags.GetMainVolumeSize(args)
    validate_only = flags.GetValidateOnly(args)
    tags = flags.GetTags(args)
    admin_users = args.admin_users if args.admin_users else [
        properties.VALUES.core.account.Get()
    ]
    async_ = getattr(args, "async_", False)
    fleet_project = flags.GetFleetProject(args)
    service_load_balancer_subnet_id = args.service_load_balancer_subnet_id
    endpoint_subnet_id = args.endpoint_subnet_id
    database_encryption_key_id = args.database_encryption_key_id
    config_encryption_key_id = args.config_encryption_key_id
    config_encryption_public_key = args.config_encryption_public_key

    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseAzureClusterResourceArg(args).locationsId,
        self.ReleaseTrack()):
      # Parsing again after endpoint override is set.
      cluster_ref = resource_args.ParseAzureClusterResourceArg(args)
      client_ref = resource_args.ParseAzureClientResourceArg(args)
      cluster_client = azure_api_util.ClustersClient(track=self.ReleaseTrack())
      op = cluster_client.Create(
          cluster_ref=cluster_ref,
          client_ref=client_ref,
          azure_region=azure_region,
          resource_group_id=resource_group_id,
          vnet_id=vnet_id,
          pod_address_cidr_blocks=pod_address_cidr_blocks,
          service_address_cidr_blocks=service_address_cidr_blocks,
          cluster_version=cluster_version,
          subnet_id=subnet_id,
          vm_size=vm_size,
          ssh_public_key=ssh_public_key,
          proxy_resource_group_id=proxy_resource_group_id,
          proxy_secret_id=proxy_secret_id,
          root_volume_size=root_volume_size,
          main_volume_size=main_volume_size,
          validate_only=validate_only,
          tags=tags,
          admin_users=admin_users,
          replica_placements=replica_placements,
          fleet_project=fleet_project,
          service_load_balancer_subnet_id=service_load_balancer_subnet_id,
          endpoint_subnet_id=endpoint_subnet_id,
          database_encryption_key_id=database_encryption_key_id,
          config_encryption_key_id=config_encryption_key_id,
          config_encryption_public_key=config_encryption_public_key)

      if validate_only:
        args.format = "disable"
        return

      op_ref = resource_args.GetOperationResource(op)
      log.CreatedResource(op_ref, kind=constants.LRO_KIND)

      if not async_:
        op_client = operations.Client(track=self.ReleaseTrack())
        op_client.Wait(
            op_ref, "Creating cluster {} in Azure region {}".format(
                cluster_ref.azureClustersId, azure_region))

      log.CreatedResource(
          cluster_ref, kind=constants.AZURE_CLUSTER_KIND, is_async=async_)
      return cluster_client.Get(cluster_ref)
