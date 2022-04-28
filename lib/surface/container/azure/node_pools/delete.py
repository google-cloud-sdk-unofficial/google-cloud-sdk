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

"""Command to delete a node pool in an Anthos cluster on Azure."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container import util as gke_util
from googlecloudsdk.api_lib.container.gkemulticloud import azure as azure_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.azure import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import operations
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


_EXAMPLES = """
To delete a node pool named ``my-node-pool'' in a cluster named ``my-cluster''
managed in location ``us-west1'', run:

$ {command} my-node-pool --cluster=my-cluster --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a node pool in an Anthos cluster on Azure."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddAzureNodePoolResourceArg(parser, 'to delete')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run the delete command."""

    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseAzureNodePoolResourceArg(args).locationsId,
        self.ReleaseTrack()):
      # Parsing again after endpoint override is set.
      nodepool_ref = resource_args.ParseAzureNodePoolResourceArg(args)
      api_client = azure_api_util.NodePoolsClient()
      api_client.Delete(nodepool_ref, validate_only=True)
      cluster = azure_api_util.ClustersClient().Get(nodepool_ref.Parent())
      console_io.PromptContinue(
          message=gke_util.ConstructList(
              'The following node pool will be deleted:', [
                  '[{name}] in [{region}/{cluster}]'.format(
                      cluster=nodepool_ref.azureClustersId,
                      name=nodepool_ref.azureNodePoolsId,
                      region=cluster.azureRegion)
              ]),
          throw_if_unattended=True,
          cancel_on_no=True)

      op = api_client.Delete(nodepool_ref)
      op_ref = resource_args.GetOperationResource(op)
      log.CreatedResource(op_ref, kind=constants.LRO_KIND)

      async_ = args.async_
      if not async_:
        op_client = operations.Client()
        op_client.Wait(
            op_ref,
            'Deleting node pool {}'.format(nodepool_ref.azureNodePoolsId))

      log.DeletedResource(
          nodepool_ref, kind=constants.AZURE_NODEPOOL_KIND, is_async=async_)
