# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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

"""Command for creating managed instance group resize requests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.compute.instance_groups.managed.resize_requests import flags as rr_flags
from googlecloudsdk.core.util import times


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(base.CreateCommand):
  """Create a Compute Engine managed instance group resize request."""

  detailed_help = {
      'brief': 'Create a Compute Engine managed instance group resize request.',
      'EXAMPLES': """

     To create a queued managed instance group resize request, run the following command:

       $ {command} my-mig --resize-request=resize-request-1 --resize-by=1
   """,
  }

  @classmethod
  def Args(cls, parser):
    instance_groups_flags.MakeZonalInstanceGroupManagerArg().AddArgument(parser)
    parser.display_info.AddFormat(rr_flags.DEFAULT_CREATE_OR_LIST_FORMAT_BETA)
    parser.add_argument(
        '--resize-request',
        metavar='RESIZE_REQUEST_NAME',
        type=str,
        required=True,
        help="""The name of the resize request to create.""",
    )
    parser.add_argument(
        '--resize-by',
        type=int,
        required=True,
        help="""The number of VMs to resize managed instance group by.""",
    )

  def Run(self, args):
    """Creates and issues an instanceGroupManagerResizeRequests.insert request.

    Args:
      args: the argparse arguments that this command was invoked with.

    Returns:
      List containing the created resize request.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    resource_arg = instance_groups_flags.MakeZonalInstanceGroupManagerArg()
    default_scope = compute_scope.ScopeEnum.ZONE
    scope_lister = flags.GetDefaultScopeLister(holder.client)
    igm_ref = resource_arg.ResolveAsResource(
        args,
        holder.resources,
        default_scope=default_scope,
        scope_lister=scope_lister,
    )

    resize_request = client.messages.InstanceGroupManagerResizeRequest(
        name=args.resize_request, resizeBy=args.resize_by
    )

    request = (
        client.messages.ComputeInstanceGroupManagerResizeRequestsInsertRequest(
            instanceGroupManager=igm_ref.Name(),
            instanceGroupManagerResizeRequest=resize_request,
            project=igm_ref.project,
            zone=igm_ref.zone,
        )
    )
    return client.MakeRequests([(
        client.apitools_client.instanceGroupManagerResizeRequests,
        'Insert',
        request,
    )])


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base.CreateCommand):
  """Create a Compute Engine managed instance group resize request."""

  detailed_help = {
      'brief': 'Create a Compute Engine managed instance group resize request.',
      'EXAMPLES': """
     To create a managed instance group resize request that succeeds only if all the VMs are immediately provisioned, run the following command:

       $ {command} my-mig --resize-request=resize-request-1 --resize-by=1

     To create a queued managed instance group resize request, run the following command:

       $ {command} my-mig --resize-request=resize-request-1 --resize-by=1 --valid-until-duration=4h
   """,
  }

  @classmethod
  def Args(cls, parser):
    instance_groups_flags.MakeZonalInstanceGroupManagerArg().AddArgument(parser)
    parser.display_info.AddFormat(rr_flags.DEFAULT_CREATE_OR_LIST_FORMAT_ALPHA)
    parser.add_argument(
        '--resize-request',
        metavar='RESIZE_REQUEST_NAME',
        type=str,
        required=True,
        help="""The name of the resize request to create.""",
    )

    count_resize_by_group = parser.add_group(mutex=True, required=True)
    count_resize_by_group.add_argument(
        '--count',
        type=int,
        help="""(ALPHA only) The number of VMs to create."""
    )
    count_resize_by_group.add_argument(
        '--resize-by',
        type=int,
        help="""The number of VMs to resize managed instance group by.""",
    )

    valid_until_group = parser.add_group(mutex=True, required=False)
    valid_until_group.add_argument(
        '--valid-until-duration',
        type=arg_parsers.Duration(),
        help="""Relative deadline for waiting for capacity.""")
    valid_until_group.add_argument(
        '--valid-until-time',
        type=arg_parsers.Datetime.Parse,
        help="""Absolute deadline for waiting for capacity in RFC3339 text format."""
    )

  def Run(self, args):
    """Creates and issues an instanceGroupManagerResizeRequests.insert request.

    Args:
      args: the argparse arguments that this command was invoked with.

    Returns:
      List containing the created resize request with its queuing policy.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    resource_arg = instance_groups_flags.MakeZonalInstanceGroupManagerArg()
    default_scope = compute_scope.ScopeEnum.ZONE
    scope_lister = flags.GetDefaultScopeLister(holder.client)
    igm_ref = resource_arg.ResolveAsResource(
        args,
        holder.resources,
        default_scope=default_scope,
        scope_lister=scope_lister,
    )

    if args.IsKnownAndSpecified('valid_until_duration'):
      queuing_policy = client.messages.QueuingPolicy(
          validUntilDuration=client.messages.Duration(
              seconds=args.valid_until_duration
          )
      )
    elif args.IsKnownAndSpecified('valid_until_time'):
      queuing_policy = client.messages.QueuingPolicy(
          validUntilTime=times.FormatDateTime(args.valid_until_time)
      )
    else:
      queuing_policy = None

    if args.IsKnownAndSpecified('resize_by'):
      resize_request = client.messages.InstanceGroupManagerResizeRequest(
          name=args.resize_request,
          queuingPolicy=queuing_policy,
          resizeBy=args.resize_by,
      )
    else:
      resize_request = client.messages.InstanceGroupManagerResizeRequest(
          name=args.resize_request,
          queuingPolicy=queuing_policy,
          resizeBy=args.count,
      )

    request = (
        client.messages.ComputeInstanceGroupManagerResizeRequestsInsertRequest(
            instanceGroupManager=igm_ref.Name(),
            instanceGroupManagerResizeRequest=resize_request,
            project=igm_ref.project,
            zone=igm_ref.zone,
        )
    )
    return client.MakeRequests([(
        client.apitools_client.instanceGroupManagerResizeRequests,
        'Insert',
        request,
    )])
