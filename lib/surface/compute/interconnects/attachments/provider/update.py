# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Command for updating partner provider interconnect attachments."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.interconnects.attachments import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.interconnects.attachments import flags as attachment_flags


class Update(base.UpdateCommand):
  """Update a Google Compute Engine partner provider interconnect attachment.

  *{command}* is used to update partner provider interconnect attachments. An
  interconnect attachment binds the underlying connectivity of an Interconnect
  to a path into and out of the customer's cloud network.
  """
  INTERCONNECT_ATTACHMENT_ARG = None
  INTERCONNECT_ARG = None
  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):

    cls.INTERCONNECT_ATTACHMENT_ARG = (
        attachment_flags.InterconnectAttachmentArgument())
    cls.INTERCONNECT_ATTACHMENT_ARG.AddArgument(parser, operation_type='patch')
    attachment_flags.AddBandwidth(parser, required=False)
    attachment_flags.AddPartnerMetadata(parser, required=False)
    attachment_flags.AddDescription(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    attachment_ref = self.INTERCONNECT_ATTACHMENT_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    interconnect_attachment = client.InterconnectAttachment(
        attachment_ref, compute_client=holder.client)

    return interconnect_attachment.PatchAlpha(
        description=args.description,
        bandwidth=args.bandwidth,
        partner_name=args.partner_name,
        partner_interconnect=args.partner_interconnect,
        partner_portal_url=args.partner_portal_url)
