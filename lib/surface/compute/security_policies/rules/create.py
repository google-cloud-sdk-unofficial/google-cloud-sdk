# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command for creating security policies rules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.security_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.security_policies import flags as security_policies_flags
from googlecloudsdk.command_lib.compute.security_policies import security_policies_utils
from googlecloudsdk.command_lib.compute.security_policies.rules import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class CreateHelper(object):
  r"""Create a Compute Engine security policy rule.

  *{command}* is used to create security policy rules.

  ## EXAMPLES

  To create a rule at priority 1000 to block the IP range
  1.2.3.0/24, run:

    $ {command} 1000 \
       --action=deny-403 \
       --security-policy=my-policy \
       --description="block 1.2.3.0/24" \
       --src-ip-ranges=1.2.3.0/24
  """

  @classmethod
  def Args(
      cls,
      parser,
      support_fairshare=False,
      support_rpc_status=False,
  ):
    """Generates the flagset for a Create command."""
    cls.NAME_ARG = (flags.PriorityArgument('add'))
    cls.NAME_ARG.AddArgument(
        parser, operation_type='add', cust_metavar='PRIORITY')
    flags.AddRegionFlag(parser, 'add')
    cls.SECURITY_POLICY_ARG = (
        security_policies_flags.SecurityPolicyMultiScopeArgumentForRules())
    cls.SECURITY_POLICY_ARG.AddArgument(parser)
    flags.AddMatcherAndNetworkMatcher(parser)
    flags.AddAction(
        parser,
        support_fairshare=support_fairshare)
    flags.AddDescription(parser)
    flags.AddPreview(parser, default=None)
    flags.AddRedirectOptions(parser)
    flags.AddRateLimitOptions(
        parser,
        support_rpc_status=support_rpc_status,
    )
    flags.AddRequestHeadersToAdd(parser)
    flags.AddRecaptchaOptions(parser)
    parser.display_info.AddCacheUpdater(
        security_policies_flags.SecurityPoliciesCompleter)

  @classmethod
  def Run(
      cls,
      release_track,
      args,
      support_rpc_status,
  ):
    """Validates arguments and creates a security policy rule."""
    holder = base_classes.ComputeApiHolder(release_track)
    if args.security_policy:
      security_policy_ref = cls.SECURITY_POLICY_ARG.ResolveAsResource(
          args,
          holder.resources,
          default_scope=compute_scope.ScopeEnum.GLOBAL)
      if getattr(security_policy_ref, 'region', None) is not None:
        ref = holder.resources.Parse(
            args.name,
            collection='compute.regionSecurityPolicyRules',
            params={
                'project': properties.VALUES.core.project.GetOrFail,
                'region': security_policy_ref.region,
                'securityPolicy': args.security_policy,
            })
      else:
        ref = holder.resources.Parse(
            args.name,
            collection='compute.securityPolicyRules',
            params={
                'project': properties.VALUES.core.project.GetOrFail,
                'securityPolicy': args.security_policy,
            },
        )
    else:
      try:
        ref = holder.resources.Parse(
            args.name,
            collection='compute.regionSecurityPolicyRules',
            params={
                'project': properties.VALUES.core.project.GetOrFail,
                'region': getattr(args, 'region', None),
            },
        )
      except (
          resources.RequiredFieldOmittedException,
          resources.WrongResourceCollectionException,
      ):
        ref = holder.resources.Parse(
            args.name,
            collection='compute.securityPolicyRules',
            params={
                'project': properties.VALUES.core.project.GetOrFail,
            },
        )

    security_policy_rule = client.SecurityPolicyRule(
        ref, compute_client=holder.client)

    redirect_options = security_policies_utils.CreateRedirectOptions(
        holder.client, args
    )
    rate_limit_options = security_policies_utils.CreateRateLimitOptions(
        holder.client,
        args,
        support_rpc_status,
    )

    request_headers_to_add = args.request_headers_to_add

    expression_options = security_policies_utils.CreateExpressionOptions(
        holder.client, args
    )

    network_matcher = security_policies_utils.CreateNetworkMatcher(
        holder.client, args
    )[0]

    return security_policy_rule.Create(
        src_ip_ranges=args.src_ip_ranges,
        expression=args.expression,
        expression_options=expression_options,
        network_matcher=network_matcher,
        action=args.action,
        description=args.description,
        preview=args.preview,
        redirect_options=redirect_options,
        rate_limit_options=rate_limit_options,
        request_headers_to_add=request_headers_to_add,
    )


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base.CreateCommand):
  r"""Create a Compute Engine security policy rule.

  *{command}* is used to create security policy rules.

  ## EXAMPLES

  To create a rule at priority 1000 to block the IP range
  1.2.3.0/24, run:

    $ {command} 1000 \
       --action=deny-403 \
       --security-policy=my-policy \
       --description="block 1.2.3.0/24" \
       --src-ip-ranges=1.2.3.0/24
  """

  SECURITY_POLICY_ARG = None
  NAME_ARG = None

  _support_rpc_status = False

  @classmethod
  def Args(cls, parser):
    CreateHelper.Args(
        parser,
        support_rpc_status=cls._support_rpc_status,
    )

  def Run(self, args):
    return CreateHelper.Run(
        self.ReleaseTrack(),
        args,
        support_rpc_status=self._support_rpc_status,
    )


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(base.CreateCommand):
  r"""Create a Compute Engine security policy rule.

  *{command}* is used to create security policy rules.

  ## EXAMPLES

  To create a rule at priority 1000 to block the IP range
  1.2.3.0/24, run:

    $ {command} 1000 \
       --action=deny-403 \
       --security-policy=my-policy \
       --description="block 1.2.3.0/24" \
       --src-ip-ranges=1.2.3.0/24
  """

  SECURITY_POLICY_ARG = None

  _support_rpc_status = False

  @classmethod
  def Args(cls, parser):
    CreateHelper.Args(
        parser,
        support_fairshare=True,
        support_rpc_status=cls._support_rpc_status,
    )

  def Run(self, args):
    return CreateHelper.Run(
        self.ReleaseTrack(),
        args,
        support_rpc_status=self._support_rpc_status,
    )


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base.CreateCommand):
  r"""Create a Compute Engine security policy rule.

  *{command}* is used to create security policy rules.

  ## EXAMPLES

  To create a rule at priority 1000 to block the IP range
  1.2.3.0/24, run:

    $ {command} 1000 \
       --action=deny-403 \
       --security-policy=my-policy \
       --description="block 1.2.3.0/24" \
       --src-ip-ranges=1.2.3.0/24
  """

  SECURITY_POLICY_ARG = None

  _support_rpc_status = True

  @classmethod
  def Args(cls, parser):
    CreateHelper.Args(
        parser,
        support_fairshare=True,
        support_rpc_status=cls._support_rpc_status,
    )

  def Run(self, args):
    return CreateHelper.Run(
        self.ReleaseTrack(),
        args,
        support_rpc_status=self._support_rpc_status,
    )
