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
"""Command to create a new GKE cluster on AWS."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.aws import clusters
from googlecloudsdk.command_lib.container.aws import flags as aws_flags
from googlecloudsdk.command_lib.container.aws import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.command_lib.container.gkemulticloud import operations
from googlecloudsdk.core import log

# Command needs to be in one line for the docgen tool to format properly.
_EXAMPLES = """
To create a cluster named ``my-cluster'' managed in location ``us-west1'',
run:

$ {command} my-cluster --location=us-west1 --aws-region=AWS_REGION --cluster-version=CLUSTER_VERSION --database-encryption-kms-key-arn=KMS_KEY_ARN --iam-instance-profile=IAM_INSTANCE_PROFILE --pod-address-cidr-blocks=POD_ADDRESS_CIDR_BLOCKS --role-arn=ROLE_ARN --service-address-cidr-blocks=SERVICE_ADDRESS_CIDR_BLOCKS --service-load-balancer-subnet-ids=SUBNET_ID --subnet-ids=SUBNET_ID --vpc-id=VPC_ID
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a GKE cluster on AWS."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    resource_args.AddAwsClusterResourceArg(parser, 'to create')

    parser.add_argument(
        '--subnet-ids',
        required=True,
        type=arg_parsers.ArgList(),
        metavar='SUBNET_ID',
        help='Subnet ID of an existing VNET to use for the cluster control plane.'
    )

    flags.AddPodAddressCidrBlocks(parser)
    flags.AddServiceAddressCidrBlocks(parser)
    flags.AddClusterVersion(parser)
    flags.AddRootVolumeSize(parser)
    flags.AddMainVolumeSize(parser)
    flags.AddValidateOnly(parser, 'cluster to create')
    flags.AddFleetProject(parser)
    flags.AddTags(parser, 'cluster')

    aws_flags.AddAwsRegion(parser)
    aws_flags.AddServiceLoadBalancerSubnetIDs(parser)
    aws_flags.AddIamInstanceProfile(parser)
    aws_flags.AddInstanceType(parser)
    aws_flags.AddSshEC2KeyPair(parser)
    aws_flags.AddConfigEncryptionKmsKeyArn(parser)
    aws_flags.AddDatabaseEncryptionKmsKeyArn(parser)
    aws_flags.AddRoleArn(parser)
    aws_flags.AddRoleSessionName(parser)
    aws_flags.AddVpcId(parser)
    aws_flags.AddSecurityGroupIds(parser, 'control plane replicas')
    aws_flags.AddRootVolumeType(parser)
    aws_flags.AddRootVolumeIops(parser)
    aws_flags.AddRootVolumeKmsKeyArn(parser)
    aws_flags.AddMainVolumeType(parser)
    aws_flags.AddMainVolumeIops(parser)
    aws_flags.AddMainVolumeKmsKeyArn(parser)
    aws_flags.AddProxyConfig(parser)

    base.ASYNC_FLAG.AddToParser(parser)

    parser.display_info.AddFormat(clusters.CLUSTERS_FORMAT)

  def Run(self, args):
    """Runs the create command."""
    release_track = self.ReleaseTrack()

    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseAwsClusterResourceArg(args).locationsId,
        release_track):
      # Parsing again after endpoint override is set.
      cluster_ref = resource_args.ParseAwsClusterResourceArg(args)
      cluster_client = clusters.Client(track=release_track)
      args.root_volume_size = flags.GetRootVolumeSize(args)
      args.root_volume_type = aws_flags.GetRootVolumeType(args)
      args.main_volume_size = flags.GetMainVolumeSize(args)
      args.main_volume_type = aws_flags.GetMainVolumeType(args)
      args.fleet_project = flags.GetFleetProject(args)
      op = cluster_client.Create(cluster_ref, args)
      op_ref = resource_args.GetOperationResource(op)

      validate_only = getattr(args, 'validate_only', False)
      if validate_only:
        args.format = 'disable'
        return

      log.CreatedResource(op_ref, kind=constants.LRO_KIND)

      async_ = getattr(args, 'async_', False)
      if not async_:
        op_client = operations.Client(track=release_track)
        op_client.Wait(
            op_ref, 'Creating cluster {} in AWS region {}'.format(
                cluster_ref.awsClustersId, args.aws_region))

      log.CreatedResource(
          cluster_ref, kind=constants.AWS_CLUSTER_KIND, is_async=async_)
      return cluster_client.Get(cluster_ref)
