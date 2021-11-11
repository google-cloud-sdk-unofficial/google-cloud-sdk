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

"""Command to delete an Azure cluster."""

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

_EXAMPLES = """
To delete a cluster named ``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-cluster --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete an Azure cluster."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddAzureClusterResourceArg(parser, 'to delete')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run the delete command."""

    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseAzureClusterResourceArg(args).locationsId,
        self.ReleaseTrack()):
      # Parsing again after endpoint override is set.
      cluster_ref = resource_args.ParseAzureClusterResourceArg(args)
      api_client = azure_api_util.ClustersClient(track=self.ReleaseTrack())

      cluster = api_client.Get(cluster_ref)
      console_io.PromptContinue(
          message=gke_util.ConstructList(
              'The following Azure cluster will be deleted:', [
                  '[{name}] in [{region}]'.format(
                      name=cluster_ref.azureClustersId,
                      region=cluster.azureRegion)
              ]),
          throw_if_unattended=True,
          cancel_on_no=True)

      op = api_client.Delete(cluster_ref)
      op_ref = resource_args.GetOperationResource(op)
      log.CreatedResource(op_ref, kind=constants.LRO_KIND)

      async_ = args.async_
      if not async_:
        waiter.WaitFor(
            waiter.CloudOperationPollerNoResources(
                api_client.client.projects_locations_operations),
            op_ref,
            'Deleting cluster {}'.format(cluster_ref.azureClustersId),
            wait_ceiling_ms=constants.MAX_LRO_POLL_INTERVAL_MS)

      log.DeletedResource(
          cluster_ref, kind=constants.AZURE_CLUSTER_KIND, is_async=async_)
