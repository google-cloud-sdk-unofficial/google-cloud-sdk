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
from googlecloudsdk.calliope import exceptions
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


class UpdateHelper(object):
  """Update a Google Compute Engine service attachment."""

  SERVICE_ATTACHMENT_ARG = None
  NAT_SUBNETWORK_ARG = None

  def __init__(
      self,
      holder,
      support_endpoint_based_security_arg,
  ):
    self._holder = holder
    self._support_endpoint_based_security_arg = (
        support_endpoint_based_security_arg
    )

  @classmethod
  def Args(
      cls,
      parser,
      support_endpoint_based_security_arg,
  ):
    """Create a Google Compute Engine service attachment.

    Args:
      parser: the parser that parses the input from the user.
      support_endpoint_based_security_arg: Whether to support endpoint based
        security.

    cls: Hold onto the definition of a complex argument so it can be used later
      to process the user's input.
    flags: Define and register command-line arguments with the argument parser.
    """
    cls.SERVICE_ATTACHMENT_ARG = flags.ServiceAttachmentArgument()
    cls.SERVICE_ATTACHMENT_ARG.AddArgument(parser, operation_type='update')
    cls.NAT_SUBNETWORK_ARG = (
        subnetwork_flags.SubnetworkArgumentForServiceAttachment(required=False)
    )
    cls.NAT_SUBNETWORK_ARG.AddArgument(parser)

    flags.AddDescription(parser)
    flags.AddTargetServiceArgsForUpdate(parser)
    flags.AddConnectionPreference(parser, is_update=True)
    flags.AddEnableProxyProtocolForUpdate(parser)
    flags.AddReconcileConnectionsForUpdate(parser)
    flags.AddConsumerRejectList(parser)
    if support_endpoint_based_security_arg:
      flags.AddConsumerAcceptList(parser)
      flags.AddRemoveObsoleteEndpointEntries(parser)
    else:
      flags.AddConsumerAcceptListOld(parser)
    flags.AddPropagatedConnectionLimit(parser)

  def _GetConsumerAcceptList(self, args, holder):
    if self._support_endpoint_based_security_arg:
      return service_attachments_utils.GetConsumerAcceptListWithEndpointBasedSecurity(
          args, holder.client.messages
      )
    return service_attachments_utils.GetConsumerAcceptList(
        args, holder.client.messages
    )

  def _GetProjectOrNetworkOrEndpointBasedOnArg(self, consumer_limit):
    if self._support_endpoint_based_security_arg:
      return self._GetProjectOrNetworkOrEndpoint(consumer_limit)
    return self._GetProjectOrNetwork(consumer_limit)

  def _GetProjectOrNetwork(self, consumer_limit):
    if consumer_limit.projectIdOrNum is not None:
      return (consumer_limit.projectIdOrNum, consumer_limit.connectionLimit)
    return (consumer_limit.networkUrl, consumer_limit.connectionLimit)

  def _GetProjectOrNetworkOrEndpoint(self, consumer_limit):
    if consumer_limit.projectIdOrNum is not None:
      return (consumer_limit.projectIdOrNum, consumer_limit.connectionLimit)
    elif consumer_limit.endpointUrl is not None:
      return (consumer_limit.endpointUrl, consumer_limit.connectionLimit)
    return (consumer_limit.networkUrl, consumer_limit.connectionLimit)

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
    assert self.NAT_SUBNETWORK_ARG
    nat_subnetwork_refs = self.NAT_SUBNETWORK_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.REGION,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    if nat_subnetwork_refs is None:
      return []
    nat_subnetworks = [
        nat_subnetwork_ref.SelfLink()
        for nat_subnetwork_ref in nat_subnetwork_refs
    ]
    return nat_subnetworks

  def _RemoveObsoleteEndpointEntries(self, replacement, cleared_fields):
    """Removes obsolete endpoint entries from accept and reject lists."""
    is_updated = False
    connected_endpoint_ids = service_attachments_utils.GetConnectedEndpointIds(
        replacement
    )
    # Remove endpoint URLs that are no longer valid from consumer accept list.
    if service_attachments_utils.CleanObsoleteAcceptedEndpointUrls(
        replacement, connected_endpoint_ids, cleared_fields
    ):
      is_updated = True

    # Remove endpoint URLs that are no longer valid from consumer reject list.
    if service_attachments_utils.CleanObsoleteRejectedEndpointUrls(
        replacement, connected_endpoint_ids, cleared_fields
    ):
      is_updated = True
    return is_updated

  def _Modify(self, holder, args, old_resource, cleared_fields):
    """Returns the updated service attachment."""
    replacement = encoding.CopyProtoMessage(old_resource)
    is_updated = False

    if args.IsSpecified('target_service'):
      is_updated = True
      replacement.targetService = args.target_service

    if args.IsSpecified('description'):
      if args.description != old_resource.description:
        replacement.description = args.description
        is_updated = True

    if args.IsSpecified('connection_preference'):
      new_connection_preference = (
          service_attachments_utils.GetConnectionPreference(
              args, holder.client.messages
          )
      )
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
      consumer_accept_list = self._GetConsumerAcceptList(args, holder)
      new_accept_list = sorted(
          consumer_accept_list,
          key=self._GetProjectOrNetworkOrEndpointBasedOnArg,
      )
      if old_resource.consumerAcceptLists is None or new_accept_list != sorted(
          old_resource.consumerAcceptLists,
          key=self._GetProjectOrNetworkOrEndpointBasedOnArg,
      ):
        replacement.consumerAcceptLists = new_accept_list
        is_updated = True
        if not new_accept_list:
          # The user can clear up the accept list
          cleared_fields.append('consumerAcceptLists')

    if (
        self._support_endpoint_based_security_arg
        and args.remove_obsolete_endpoint_accept_reject_entries
    ):
      if args.IsSpecified(
          'consumer_accept_list'
      ) or args.IsSpecified('consumer_reject_list'):
        raise exceptions.ConflictingArgumentsException(
            '--remove-obsolete-endpoint-accept-reject-entries cannot be '
            'specified with --consumer-accept-list or --consumer-reject-list.'
        )
      is_updated = self._RemoveObsoleteEndpointEntries(
          replacement, cleared_fields
      )

    if args.IsSpecified('reconcile_connections'):
      if args.reconcile_connections != old_resource.reconcileConnections:
        replacement.reconcileConnections = args.reconcile_connections
        is_updated = True

    if args.IsSpecified('propagated_connection_limit'):
      if (
          args.propagated_connection_limit
          != old_resource.propagatedConnectionLimit
      ):
        replacement.propagatedConnectionLimit = args.propagated_connection_limit
        is_updated = True

    if is_updated:
      return replacement
    return None

  def Run(self, args):
    """Issue a service attachment PATCH request."""
    client = self._holder.client
    assert self.SERVICE_ATTACHMENT_ARG
    service_attachment_ref = self.SERVICE_ATTACHMENT_ARG.ResolveAsResource(
        args,
        self._holder.resources,
        default_scope=compute_scope.ScopeEnum.REGION,
    )
    old_resource = self._GetOldResource(client, service_attachment_ref)
    cleared_fields = []
    replacement = self._Modify(self._holder, args, old_resource, cleared_fields)
    if replacement is None:
      return old_resource

    with client.apitools_client.IncludeFields(cleared_fields):
      return client.MakeRequests(
          [self._GetPatchRequest(client, service_attachment_ref, replacement)])


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Google Compute Engine service attachment."""
  _support_endpoint_based_security_arg = False
  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    UpdateHelper.Args(
        parser,
        cls._support_endpoint_based_security_arg,
    )

  def Run(self, args):
    """Issue a service attachment PATCH request."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return UpdateHelper(
        holder,
        self._support_endpoint_based_security_arg,
    ).Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update a Google Compute Engine service attachment."""
  _support_endpoint_based_security_arg = True
  detailed_help = _DetailedHelp()


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Update a Google Compute Engine service attachment."""
  detailed_help = _DetailedHelp()
