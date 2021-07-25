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

"""Command to delete an Azure node pool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container import util as gke_util
from googlecloudsdk.api_lib.container.azure import util as azure_api_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.azure import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete an Azure node pool."""

  @staticmethod
  def Args(parser):
    resource_args.AddAzureNodePoolResourceArg(parser, 'to delete')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run the delete command."""
    nodepool_ref = resource_args.ParseAzureNodePoolResourceArg(args)
    async_ = args.async_

    with endpoint_util.GkemulticloudEndpointOverride(nodepool_ref.locationsId,
                                                     self.ReleaseTrack()):
      api_client = azure_api_util.NodePoolsClient(track=self.ReleaseTrack())
      api_client.Delete(nodepool_ref, validate_only=True)
      cluster = azure_api_util.ClustersClient(
          track=self.ReleaseTrack()).Get(nodepool_ref.Parent())
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
      if not async_:
        waiter.WaitFor(
            waiter.CloudOperationPollerNoResources(
                api_client.client.projects_locations_operations),
            op_ref,
            'Deleting node pool {}'.format(nodepool_ref.azureNodePoolsId),
            wait_ceiling_ms=constants.MAX_LRO_POLL_INTERVAL_MS)

      log.DeletedResource(nodepool_ref, kind='Azure Node Pool')
