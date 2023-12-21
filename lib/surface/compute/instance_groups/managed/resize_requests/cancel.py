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

"""Command for cancelling queued resize requests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Cancel(base.UpdateCommand):
  """Cancel a Compute Engine managed instance group resize request.

  *{command}* cancels a Compute Engine managed instance group resize request.

  You can only cancel a resize request when it is in the ACCEPTED state.
  """

  @classmethod
  def Args(cls, parser):
    instance_groups_flags.MakeZonalInstanceGroupManagerArg().AddArgument(
        parser)
    parser.add_argument(
        '--resize-request',
        metavar='RESIZE_REQUEST_NAME',
        type=str,
        required=True,
        help="""The name of the resize request to cancel.""")

  def Run(self, args):
    """Creates and issues an instanceGroupManagerResizeRequests.cancel request.

    Args:
      args: the argparse arguments that this command was invoked with.

    Returns:
      A URI path of the successfully canceled resize request.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    resource_arg = instance_groups_flags.MakeZonalInstanceGroupManagerArg()
    default_scope = compute_scope.ScopeEnum.ZONE
    scope_lister = flags.GetDefaultScopeLister(client)
    igm_ref = resource_arg.ResolveAsResource(
        args,
        holder.resources,
        default_scope=default_scope,
        scope_lister=scope_lister)

    requests = [(
        client.apitools_client.instanceGroupManagerResizeRequests,
        'Cancel',
        client.messages.ComputeInstanceGroupManagerResizeRequestsCancelRequest(
            project=igm_ref.project,
            zone=igm_ref.zone,
            instanceGroupManager=igm_ref.instanceGroupManager,
            resizeRequest=args.resize_request,
        ),
    )]
    return client.MakeRequests(requests)

