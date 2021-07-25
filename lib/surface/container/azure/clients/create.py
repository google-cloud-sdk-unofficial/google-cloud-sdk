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

"""Command to create a new GKE cluster on Azure."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.azure import util as azure_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.azure import resource_args
from googlecloudsdk.command_lib.container.azure import util as command_util
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create an Azure client."""

  @staticmethod
  def Args(parser):
    resource_args.AddAzureClientResourceArg(parser, "to create")
    parser.add_argument(
        "--tenant-id",
        required=True,
        help="The Azure Active Directory (AAD) tenant ID (GUID) to associate with the client."
    )
    parser.add_argument(
        "--application-id",
        required=True,
        dest="app_id",
        help="The Azure Active Directory (AAD) Application/Client ID (GUID).")
    flags.AddValidateOnly(parser, "creation of the client")
    parser.display_info.AddFormat(command_util.CLIENT_FORMAT)

  def Run(self, args):
    """Run the create command."""
    client_ref = args.CONCEPTS.client.Parse()
    tenant_id = args.tenant_id
    app_id = args.app_id
    validate_only = args.validate_only

    track = base.ReleaseTrack.ALPHA
    with endpoint_util.GkemulticloudEndpointOverride(client_ref.locationsId,
                                                     track):
      api_client = azure_api_util.ClientsClient(track=track)
      api_client.Create(
          client_ref=client_ref,
          tenant_id=tenant_id,
          application_id=app_id,
          validate_only=validate_only)

      log.CreatedResource(client_ref, "Azure Client")
