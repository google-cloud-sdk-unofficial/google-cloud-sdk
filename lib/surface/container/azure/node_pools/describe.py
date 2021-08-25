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

"""Command to describe an Azure node pool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.azure import util as azure_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.azure import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util

_EXAMPLES = """
To describe a node pool named ``my-node-pool'' in a cluster named
``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-node-pool --cluster=my-cluster --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe an Azure node pool."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddAzureNodePoolResourceArg(parser, 'to describe')

  def Run(self, args):
    """Run the describe command."""

    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseAzureNodePoolResourceArg(args).locationsId,
        self.ReleaseTrack()):
      # Parsing again after endpoint override is set.
      nodepool_ref = resource_args.ParseAzureNodePoolResourceArg(args)
      client = azure_api_util.NodePoolsClient(track=self.ReleaseTrack())
      return client.Get(nodepool_ref)
