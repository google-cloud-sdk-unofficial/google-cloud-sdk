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
from googlecloudsdk.command_lib.compute.security_policies import flags as security_policies_flags
from googlecloudsdk.command_lib.compute.security_policies import security_policies_utils
from googlecloudsdk.command_lib.compute.security_policies.rules import flags
from googlecloudsdk.core import properties


class CreateHelper(object):
  r"""Create a Compute Engine security policy rule.

  *{command}* is used to create security policy rules.

  For example to create a rule at priority 1000 to block the IP range
  1.2.3.0/24, run:

        $ {command} 1000 \
            --action deny-403 \
            --security-policy my-policy \
            --description "block 1.2.3.0/24" \
            --src-ip-ranges 1.2.3.0/24
  """

  @classmethod
  def Args(cls, parser, support_redirect, support_rate_limit,
           support_header_action, support_tcp_ssl):
    """Generates the flagset for a Create command."""
    flags.AddPriority(parser, 'add')
    cls.SECURITY_POLICY_ARG = (
        security_policies_flags.SecurityPolicyArgumentForRules())
    cls.SECURITY_POLICY_ARG.AddArgument(parser)
    flags.AddMatcher(parser)
    flags.AddAction(
        parser,
        support_redirect=support_redirect,
        support_rate_limit=support_rate_limit,
        support_tcp_ssl=support_tcp_ssl)
    flags.AddDescription(parser)
    flags.AddPreview(parser, default=None)
    if support_redirect:
      flags.AddRedirectOptions(parser)
    if support_rate_limit:
      flags.AddRateLimitOptions(
          parser,
          support_tcp_ssl=support_tcp_ssl,
          support_exceed_redirect=support_redirect)
    if support_header_action:
      flags.AddRequestHeadersToAdd(parser)
    parser.display_info.AddCacheUpdater(
        security_policies_flags.GlobalSecurityPoliciesCompleter)

  @classmethod
  def Run(cls, release_track, args, support_redirect, support_rate_limit,
          support_header_action):
    """Validates arguments and creates a security policy rule."""
    holder = base_classes.ComputeApiHolder(release_track)
    ref = holder.resources.Parse(
        args.name,
        collection='compute.securityPolicyRules',
        params={
            'project': properties.VALUES.core.project.GetOrFail,
            'securityPolicy': args.security_policy
        })
    security_policy_rule = client.SecurityPolicyRule(
        ref, compute_client=holder.client)

    redirect_options = None
    rate_limit_options = None
    if support_redirect:
      redirect_options = (
          security_policies_utils.CreateRedirectOptions(holder.client, args))
    if support_rate_limit:
      rate_limit_options = (
          security_policies_utils.CreateRateLimitOptions(holder.client, args))

    request_headers_to_add = None
    if support_header_action:
      request_headers_to_add = args.request_headers_to_add

    return security_policy_rule.Create(
        src_ip_ranges=args.src_ip_ranges,
        expression=args.expression,
        action=args.action,
        description=args.description,
        preview=args.preview,
        redirect_options=redirect_options,
        rate_limit_options=rate_limit_options,
        request_headers_to_add=request_headers_to_add)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base.CreateCommand):
  r"""Create a Compute Engine security policy rule.

  *{command}* is used to create security policy rules.

  For example to create a rule at priority 1000 to block the IP range
  1.2.3.0/24, run:

        $ {command} 1000 \
            --action deny-403 \
            --security-policy my-policy \
            --description "block 1.2.3.0/24" \
            --src-ip-ranges 1.2.3.0/24
  """

  SECURITY_POLICY_ARG = None

  _support_redirect = True
  _support_rate_limit = True
  _support_header_action = True
  _support_tcl_ssl = False

  @classmethod
  def Args(cls, parser):
    CreateHelper.Args(
        parser,
        support_redirect=cls._support_redirect,
        support_rate_limit=cls._support_rate_limit,
        support_header_action=cls._support_header_action,
        support_tcp_ssl=cls._support_tcl_ssl)

  def Run(self, args):
    return CreateHelper.Run(
        self.ReleaseTrack(),
        args,
        support_redirect=self._support_redirect,
        support_rate_limit=self._support_rate_limit,
        support_header_action=self._support_header_action)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(base.CreateCommand):
  r"""Create a Compute Engine security policy rule.

  *{command}* is used to create security policy rules.

  For example to create a rule at priority 1000 to block the IP range
  1.2.3.0/24, run:

        $ {command} 1000 \
            --action deny-403 \
            --security-policy my-policy \
            --description "block 1.2.3.0/24" \
            --src-ip-ranges 1.2.3.0/24
  """

  SECURITY_POLICY_ARG = None

  _support_redirect = True
  _support_rate_limit = True
  _support_header_action = True
  _support_tcl_ssl = False

  @classmethod
  def Args(cls, parser):
    CreateHelper.Args(
        parser,
        support_redirect=cls._support_redirect,
        support_rate_limit=cls._support_rate_limit,
        support_header_action=cls._support_header_action,
        support_tcp_ssl=cls._support_tcl_ssl)

  def Run(self, args):
    return CreateHelper.Run(
        self.ReleaseTrack(),
        args,
        support_redirect=self._support_redirect,
        support_rate_limit=self._support_rate_limit,
        support_header_action=self._support_header_action)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base.CreateCommand):
  r"""Create a Compute Engine security policy rule.

  *{command}* is used to create security policy rules.

  For example to create a rule at priority 1000 to block the IP range
  1.2.3.0/24, run:

        $ {command} 1000 \
            --action deny-403 \
            --security-policy my-policy \
            --description "block 1.2.3.0/24" \
            --src-ip-ranges 1.2.3.0/24
  """

  SECURITY_POLICY_ARG = None

  _support_redirect = True
  _support_rate_limit = True
  _support_header_action = True
  _support_tcl_ssl = True

  @classmethod
  def Args(cls, parser):
    CreateHelper.Args(
        parser,
        support_redirect=cls._support_redirect,
        support_rate_limit=cls._support_rate_limit,
        support_header_action=cls._support_header_action,
        support_tcp_ssl=cls._support_tcl_ssl)

  def Run(self, args):
    return CreateHelper.Run(
        self.ReleaseTrack(),
        args,
        support_redirect=self._support_redirect,
        support_rate_limit=self._support_rate_limit,
        support_header_action=self._support_header_action)
