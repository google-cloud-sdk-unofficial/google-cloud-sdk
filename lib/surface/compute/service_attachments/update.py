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
"""Command for updating service attachments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.networks.subnets import flags as subnetwork_flags
from googlecloudsdk.command_lib.compute.service_attachments import flags
from googlecloudsdk.command_lib.compute.service_attachments import service_attachments_utils


def _DetailedHelp():
  return {
      'brief':
          'Update a Google Compute Engine service attachment.',
      'DESCRIPTION':
          """\
      *{command}* is used to update service attachments. A service producer
      creates service attachments to make a service available to consumers.
      Service consumers use Private Service Connect endpoints to privately
      forward traffic to the service attachment.
      """,
      'EXAMPLES':
          """\
      To update the connection policy of a service attachment to be ACCEPT_MANUAL, run:

        $ {command} SERVICE_ATTACHMENT_NAME --region=us-central1 --connection-preference=ACCEPT_MANUAL

      To update all supported fields of a service attachment, run:

        $ {command} SERVICE_ATTACHMENT_NAME --region=us-central1 --connection-preference=ACCEPT_AUTOMATIC --nat-subnets=MY_SUBNET1,MY_SUBNET2 --enable-proxy-protocol --consumer-reject-list=PROJECT_ID1,PROJECT_ID2 --consumer-accept-list=PROJECT_ID3=10,PROJECT_ID4=20

      """,
  }


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Google Compute Engine service attachment."""

  SERVICE_ATTACHMENT_ARG = None
  NAT_SUBNETWORK_ARG = None
  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    cls.SERVICE_ATTACHMENT_ARG = flags.ServiceAttachmentArgument()
    cls.SERVICE_ATTACHMENT_ARG.AddArgument(parser, operation_type='update')
    cls.NAT_SUBNETWORK_ARG = subnetwork_flags.SubnetworkArgumentForServiceAttachment(
        required=False)
    cls.NAT_SUBNETWORK_ARG.AddArgument(parser)

    flags.AddDescription(parser)
    flags.AddConnectionPreference(parser, is_update=True)
    flags.AddEnableProxyProtocolForUpdate(parser)
    flags.AddConsumerRejectList(parser)
    flags.AddConsumerAcceptList(parser)

  def _GetOldResource(self, client, service_attachment_ref):
    """Returns the existing ServiceAttachment resource."""
    request = client.messages.ComputeServiceAttachmentsGetRequest(
        **service_attachment_ref.AsDict())
    collection = client.apitools_client.serviceAttachments
    return client.MakeRequests([(collection, 'Get', request)])[0]

  def _GetPatchRequest(self, client, service_attachment_ref, replacement):
    """Returns a request to update the service attachment."""
    return (client.apitools_client.serviceAttachments, 'Patch',
            client.messages.ComputeServiceAttachmentsPatchRequest(
                project=service_attachment_ref.project,
                region=service_attachment_ref.region,
                serviceAttachment=service_attachment_ref.Name(),
                serviceAttachmentResource=replacement))

  def _GetNatSubnets(self, holder, args):
    """Returns nat subnetwork urls from the argument."""
    nat_subnetwork_refs = self.NAT_SUBNETWORK_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.REGION,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))
    nat_subnetworks = [
        nat_subnetwork_ref.SelfLink()
        for nat_subnetwork_ref in nat_subnetwork_refs
    ]
    return nat_subnetworks

  def _Modify(self, holder, args, old_resource, cleared_fields):
    """Returns the updated service attachment."""
    replacement = encoding.CopyProtoMessage(old_resource)
    is_updated = False

    if args.IsSpecified('description'):
      if args.description != old_resource.description:
        replacement.description = args.description
        is_updated = True

    if args.IsSpecified('connection_preference'):
      new_connection_preference = service_attachments_utils.GetConnectionPreference(
          args, holder.client.messages)
      if new_connection_preference != old_resource.connectionPreference:
        replacement.connectionPreference = new_connection_preference
        is_updated = True

    if args.IsSpecified('enable_proxy_protocol'):
      if args.enable_proxy_protocol != old_resource.enableProxyProtocol:
        replacement.enableProxyProtocol = args.enable_proxy_protocol
        is_updated = True

    if args.IsSpecified('nat_subnets'):
      new_nat_subnets = sorted(self._GetNatSubnets(holder, args))
      if old_resource.natSubnets is None or new_nat_subnets != sorted(
          old_resource.natSubnets):
        replacement.natSubnets = new_nat_subnets
        is_updated = True

    if args.IsSpecified('consumer_reject_list'):
      new_reject_list = sorted(args.consumer_reject_list)
      if old_resource.consumerRejectLists is None or new_reject_list != sorted(
          old_resource.consumerRejectLists):
        replacement.consumerRejectLists = new_reject_list
        is_updated = True
        if not new_reject_list:
          # The user can clear up the reject list
          cleared_fields.append('consumerRejectLists')

    if args.IsSpecified('consumer_accept_list'):
      consumer_accept_list = service_attachments_utils.GetConsumerAcceptList(
          args, holder.client.messages)
      new_accept_list = sorted(
          consumer_accept_list,
          key=lambda x: (x.projectIdOrNum, x.connectionLimit))
      if old_resource.consumerAcceptLists is None or new_accept_list != sorted(
          old_resource.consumerAcceptLists,
          key=lambda x: (x.projectIdOrNum, x.connectionLimit)):
        replacement.consumerAcceptLists = new_accept_list
        is_updated = True
        if not new_accept_list:
          # The user can clear up the accept list
          cleared_fields.append('consumerAcceptLists')

    if is_updated:
      return replacement
    return None

  def Run(self, args):
    """Issue a service attachment PATCH request."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    service_attachment_ref = self.SERVICE_ATTACHMENT_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.REGION)
    old_resource = self._GetOldResource(client, service_attachment_ref)
    cleared_fields = []
    replacement = self._Modify(holder, args, old_resource, cleared_fields)
    if replacement is None:
      return old_resource

    with client.apitools_client.IncludeFields(cleared_fields):
      return client.MakeRequests(
          [self._GetPatchRequest(client, service_attachment_ref, replacement)])


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Update a Google Compute Engine service attachment."""

  @classmethod
  def Args(cls, parser):
    cls.SERVICE_ATTACHMENT_ARG = flags.ServiceAttachmentArgument()
    cls.SERVICE_ATTACHMENT_ARG.AddArgument(parser, operation_type='update')
    cls.NAT_SUBNETWORK_ARG = subnetwork_flags.SubnetworkArgumentForServiceAttachment(
        required=False)
    cls.NAT_SUBNETWORK_ARG.AddArgument(parser)

    flags.AddDescription(parser)
    flags.AddConnectionPreference(parser, is_update=True)
    flags.AddEnableProxyProtocolForUpdate(parser)
    flags.AddConsumerRejectListAlpha(parser)
    flags.AddConsumerAcceptListAlpha(parser)

  def _GetProjectOrNetwork(self, consumer_limit):
    if consumer_limit.projectIdOrNum is not None:
      return (consumer_limit.projectIdOrNum, consumer_limit.connectionLimit)
    return (consumer_limit.networkUrl, consumer_limit.connectionLimit)

  def _Modify(self, holder, args, old_resource, cleared_fields):
    """Returns the updated service attachment."""
    replacement = encoding.CopyProtoMessage(old_resource)
    is_updated = False

    if args.IsSpecified('description'):
      if args.description != old_resource.description:
        replacement.description = args.description
        is_updated = True

    if args.IsSpecified('connection_preference'):
      new_connection_preference = service_attachments_utils.GetConnectionPreference(
          args, holder.client.messages)
      if new_connection_preference != old_resource.connectionPreference:
        replacement.connectionPreference = new_connection_preference
        is_updated = True

    if args.IsSpecified('enable_proxy_protocol'):
      if args.enable_proxy_protocol != old_resource.enableProxyProtocol:
        replacement.enableProxyProtocol = args.enable_proxy_protocol
        is_updated = True

    if args.IsSpecified('nat_subnets'):
      new_nat_subnets = sorted(self._GetNatSubnets(holder, args))
      if old_resource.natSubnets is None or new_nat_subnets != sorted(
          old_resource.natSubnets):
        replacement.natSubnets = new_nat_subnets
        is_updated = True

    if args.IsSpecified('consumer_reject_list'):
      new_reject_list = sorted(args.consumer_reject_list)
      if old_resource.consumerRejectLists is None or new_reject_list != sorted(
          old_resource.consumerRejectLists):
        replacement.consumerRejectLists = new_reject_list
        is_updated = True
        if not new_reject_list:
          # The user can clear up the reject list
          cleared_fields.append('consumerRejectLists')

    if args.IsSpecified('consumer_accept_list'):
      consumer_accept_list = service_attachments_utils.GetConsumerAcceptListAlpha(
          args, holder.client.messages)
      new_accept_list = sorted(
          consumer_accept_list, key=self._GetProjectOrNetwork)
      if old_resource.consumerAcceptLists is None or new_accept_list != sorted(
          old_resource.consumerAcceptLists, key=self._GetProjectOrNetwork):
        replacement.consumerAcceptLists = new_accept_list
        is_updated = True
        if not new_accept_list:
          # The user can clear up the accept list
          cleared_fields.append('consumerAcceptLists')

    if is_updated:
      return replacement
    return None
