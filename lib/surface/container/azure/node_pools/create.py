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
"""Command to create a node pool in an Anthos cluster on Azure."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.azure import util as azure_api_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.azure import resource_args
from googlecloudsdk.command_lib.container.azure import util as command_util
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.core import log


# Command needs to be in one line for the docgen tool to format properly.
_EXAMPLES = """
To create a node pool named ``my-node-pool'' in a cluster named ``my-cluster''
managed in location ``us-west1'', run:

$ {command} my-node-pool --cluster=my-cluster --location=us-west1 --node-version=NODE_VERSION --ssh-public-key=SSH_PUBLIC_KEY --subnet-id=SUBNET_ID
"""


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a node pool in an Anthos cluster on Azure."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddAzureNodePoolResourceArg(
        parser, 'to create', positional=True)

    flags.AddNodeVersion(parser)
    flags.AddAutoscaling(parser)
    flags.AddSubnetID(parser, 'the node pool')
    flags.AddVMSize(parser)
    flags.AddSSHPublicKey(parser)
    flags.AddRootVolumeSize(parser)
    flags.AddTags(parser, 'node pool')
    flags.AddValidateOnly(parser, 'creation of the node pool')
    flags.AddMaxPodsPerNode(parser)
    flags.AddNodeLabels(parser)
    flags.AddNodeTaints(parser)
    flags.AddAzureAvailabilityZone(parser)
    flags.AddProxyConfig(parser)
    flags.AddConfigEncryption(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddFormat(command_util.NODE_POOL_FORMAT)

  def Run(self, args):
    """Run the create command."""

    node_version = flags.GetNodeVersion(args)
    subnet_id = flags.GetSubnetID(args)
    vm_size = flags.GetVMSize(args)
    ssh_key = flags.GetSSHPublicKey(args)
    root_volume_size = flags.GetRootVolumeSize(args)
    tags = flags.GetTags(args)
    validate_only = flags.GetValidateOnly(args)
    max_pods_per_node = flags.GetMaxPodsPerNode(args)
    azure_availability_zone = flags.GetAzureAvailabilityZone(args)
    min_nodes, max_nodes = flags.GetAutoscalingParams(args)
    proxy_resource_group_id = args.proxy_resource_group_id
    proxy_secret_id = args.proxy_secret_id
    config_encryption_key_id = args.config_encryption_key_id
    config_encryption_public_key = args.config_encryption_public_key
    taints = flags.GetNodeTaints(args)
    labels = flags.GetNodeLabels(args)
    image_type = flags.GetImageType(args)

    async_ = args.async_

    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseAzureNodePoolResourceArg(args).locationsId,
        self.ReleaseTrack()):
      # Parsing again after endpoint override is set.
      nodepool_ref = resource_args.ParseAzureNodePoolResourceArg(args)
      api_client = azure_api_util.NodePoolsClient(track=self.ReleaseTrack())
      op = api_client.Create(
          nodepool_ref=nodepool_ref,
          node_version=node_version,
          subnet_id=subnet_id,
          vm_size=vm_size,
          ssh_public_key=ssh_key,
          proxy_resource_group_id=proxy_resource_group_id,
          proxy_secret_id=proxy_secret_id,
          root_volume_size=root_volume_size,
          tags=tags,
          validate_only=validate_only,
          min_nodes=min_nodes,
          max_nodes=max_nodes,
          max_pods_per_node=max_pods_per_node,
          taints=taints,
          labels=labels,
          azure_availability_zone=azure_availability_zone,
          config_encryption_key_id=config_encryption_key_id,
          config_encryption_public_key=config_encryption_public_key,
          image_type=image_type)

      if validate_only:
        args.format = 'disable'
        return

      op_ref = resource_args.GetOperationResource(op)
      log.CreatedResource(op_ref, kind=constants.LRO_KIND)

      if not async_:
        waiter.WaitFor(
            waiter.CloudOperationPollerNoResources(
                api_client.client.projects_locations_operations),
            op_ref,
            'Creating node pool {}'.format(nodepool_ref.azureNodePoolsId),
            wait_ceiling_ms=constants.MAX_LRO_POLL_INTERVAL_MS)

      log.CreatedResource(
          nodepool_ref, kind=constants.AZURE_NODEPOOL_KIND, is_async=async_)
      return api_client.Get(nodepool_ref)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create a node pool in an Anthos cluster on Azure."""

  @staticmethod
  def Args(parser, track=base.ReleaseTrack.ALPHA):
    """Registers alpha track flags for this command."""
    Create.Args(parser)
    flags.AddImageType(parser)
