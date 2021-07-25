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

"""Command to delete an Azure Client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container import util as gke_util
from googlecloudsdk.api_lib.container.azure import util as azure_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.azure import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete an Azure client."""

  @staticmethod
  def Args(parser):
    resource_args.AddAzureClientResourceArg(parser, 'to delete')

  def Run(self, args):
    """Run the delete command."""
    client_ref = args.CONCEPTS.client.Parse()

    with endpoint_util.GkemulticloudEndpointOverride(client_ref.locationsId,
                                                     self.ReleaseTrack()):
      api_client = azure_api_util.ClientsClient(track=self.ReleaseTrack())
      api_client.Delete(client_ref, validate_only=True)

      console_io.PromptContinue(
          message=gke_util.ConstructList(
              'The following Azure clients will be deleted:', [
                  '[{name}] in [{region}]'.format(
                      name=client_ref.azureClientsId,
                      region=client_ref.locationsId) for ref in [client_ref]
              ]),
          throw_if_unattended=True,
          cancel_on_no=True)

      api_client.Delete(client_ref)
      log.DeletedResource(client_ref, kind='Azure Client')
