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
"""Command to list node pools in an Anthos cluster on AWS."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import aws as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.aws import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util

_EXAMPLES = """
To list all node pools in a cluster named ``my-cluster''
managed in location ``us-west1'', run:

$ {command} --cluster=my-cluster --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Describe(base.ListCommand):
  """List node pools in an Anthos cluster on AWS."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddAwsClusterResourceArg(parser, 'to list', positional=False)
    parser.display_info.AddFormat(constants.AWS_NODEPOOLS_FORMAT)

  def Run(self, args):
    """Runs the list command."""
    cluster_ref = args.CONCEPTS.cluster.Parse()
    with endpoint_util.GkemulticloudEndpointOverride(cluster_ref.locationsId):
      node_pool_client = api_util.NodePoolsClient()
      items, _ = node_pool_client.List(cluster_ref, args.page_size, args.limit)
      return items
