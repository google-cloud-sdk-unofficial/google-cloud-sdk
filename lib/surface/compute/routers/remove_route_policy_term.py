# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Command for removing a route policy term of a Compute Engine router."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.routers import flags
from googlecloudsdk.command_lib.compute.routers import route_policy_utils


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class RemoveRoutePolicyTerm(base.DeleteCommand):
  """Remove a route policy term of a Compute Engine router.

  *{command}* removes a term of a route policy.
  """

  ROUTER_ARG = None

  @classmethod
  def Args(cls, parser):
    RemoveRoutePolicyTerm.ROUTER_ARG = flags.RouterArgument()
    RemoveRoutePolicyTerm.ROUTER_ARG.AddArgument(
        parser, operation_type='remove a route policy term from'
    )
    parser.add_argument(
        '--policy-name',
        help="""Name of the route policy from which the term should be removed.""",
        required=True,
    )
    parser.add_argument(
        '--priority',
        help="""Order of the term within the policy.""",
        required=True,
        type=arg_parsers.BoundedInt(lower_bound=0, upper_bound=2147483647),
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages

    service = holder.client.apitools_client.routers

    router_ref = RemoveRoutePolicyTerm.ROUTER_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )
    route_policy = service.GetRoutePolicy(
        messages.ComputeRoutersGetRoutePolicyRequest(
            **router_ref.AsDict(), policy=args.policy_name
        )
    ).resource

    term = route_policy_utils.FindPolicyTermOrRaise(route_policy, args.priority)
    route_policy.terms.remove(term)

    request = (
        service,
        'UpdateRoutePolicy',
        messages.ComputeRoutersUpdateRoutePolicyRequest(
            **router_ref.AsDict(),
            routePolicy=route_policy,
        ),
    )
    return client.MakeRequests([request])[0]
