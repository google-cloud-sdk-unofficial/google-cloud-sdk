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
"""Command for updating security policies rules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.security_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.security_policies import flags as security_policy_flags
from googlecloudsdk.command_lib.compute.security_policies import security_policies_utils
from googlecloudsdk.command_lib.compute.security_policies.rules import flags
from googlecloudsdk.core import properties


class UpdateHelper(object):
  r"""Update a Compute Engine security policy rule.

  *{command}* is used to update security policy rules.

  ## EXAMPLES

  To update the description and IP ranges of a rule at priority
  1000, run:

    $ {command} 1000 \
       --security-policy=my-policy \
       --description="block 1.2.3.4/32" \
       --src-ip-ranges=1.2.3.4/32
  """

  @classmethod
  def Args(
      cls,
      parser,
      support_redirect,
      support_rate_limit,
      support_header_action,
      support_tcp_ssl,
      support_fairshare,
      support_regional_security_policy,
      support_multiple_rate_limit_keys,
  ):
    """Generates the flagset for an Update command."""
    flags.AddPriority(parser, 'update')
    if support_regional_security_policy:
      flags.AddRegionFlag(parser, 'update')
      cls.SECURITY_POLICY_ARG = (
          security_policy_flags.SecurityPolicyMultiScopeArgumentForRules())
    else:
      cls.SECURITY_POLICY_ARG = (
          security_policy_flags.SecurityPolicyArgumentForRules())
    cls.SECURITY_POLICY_ARG.AddArgument(parser)
    flags.AddMatcher(parser, required=False)
    flags.AddAction(
        parser,
        required=False,
        support_redirect=support_redirect,
        support_rate_limit=support_rate_limit,
        support_tcp_ssl=support_tcp_ssl,
        support_fairshare=support_fairshare)
    flags.AddDescription(parser)
    flags.AddPreview(parser, default=None)
    if support_redirect:
      flags.AddRedirectOptions(parser)
    if support_rate_limit:
      flags.AddRateLimitOptions(
          parser,
          support_tcp_ssl=support_tcp_ssl,
          support_exceed_redirect=support_redirect,
          support_fairshare=support_fairshare,
          support_multiple_rate_limit_keys=support_multiple_rate_limit_keys,
      )
    if support_header_action:
      flags.AddRequestHeadersToAdd(parser)

  @classmethod
  def Run(
      cls,
      release_track,
      args,
      support_redirect,
      support_rate_limit,
      support_header_action,
      support_fairshare,
      support_regional_security_policy,
      support_multiple_rate_limit_keys,
  ):
    """Validates arguments and patches a security policy rule."""
    modified_fields = [
        args.description, args.src_ip_ranges, args.expression, args.action,
        args.preview is not None
    ]
    min_args = [
        '--description', '--src-ip-ranges', '--expression', '--action',
        '--preview'
    ]
    if support_redirect:
      modified_fields.extend([args.redirect_type, args.redirect_target])
      min_args.extend(['--redirect-type', '--redirect-target'])
    if support_header_action:
      modified_fields.extend([args.request_headers_to_add])
      min_args.extend(['--request-headers-to-add'])
    if support_rate_limit:
      modified_fields.extend([
          args.rate_limit_threshold_count,
          args.rate_limit_threshold_interval_sec, args.conform_action,
          args.exceed_action, args.enforce_on_key, args.enforce_on_key_name,
          args.ban_threshold_count, args.ban_threshold_interval_sec,
          args.ban_duration_sec
      ])

      min_args.extend([
          '--rate-limit-threshold-count', '--rate-limit-threshold-interval-sec',
          '--conform-action', '--exceed-action', '--enforce-on-key',
          '--enforce-on-key-name', '--ban-threshold-count',
          '--ban-threshold-interval-sec', '--ban-duration-sec'
      ])
      if support_fairshare:
        modified_fields.extend([
            args.exceed_action_rpc_status_code,
            args.exceed_action_rpc_status_message
        ])
        min_args.extend([
            '--exceed-action-rpc-status-code',
            '--exceed-action-rpc-status-message'
        ])
    if not any(modified_fields):
      raise exceptions.MinimumArgumentException(
          min_args, 'At least one property must be modified.')

    holder = base_classes.ComputeApiHolder(release_track)
    ref = None
    if support_regional_security_policy:
      security_policy_ref = cls.SECURITY_POLICY_ARG.ResolveAsResource(
          args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
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
            })
    else:
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
      rate_limit_options = security_policies_utils.CreateRateLimitOptions(
          holder.client,
          args,
          support_fairshare,
          support_multiple_rate_limit_keys,
      )

    request_headers_to_add = None
    if support_header_action:
      request_headers_to_add = args.request_headers_to_add

    return security_policy_rule.Patch(
        src_ip_ranges=args.src_ip_ranges,
        expression=args.expression,
        action=args.action,
        description=args.description,
        preview=args.preview,
        redirect_options=redirect_options,
        rate_limit_options=rate_limit_options,
        request_headers_to_add=request_headers_to_add)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateGA(base.UpdateCommand):
  r"""Update a Compute Engine security policy rule.

  *{command}* is used to update security policy rules.

  ## EXAMPLES

  To update the description and IP ranges of a rule at priority
  1000, run:

    $ {command} 1000 \
       --security-policy=my-policy \
       --description="block 1.2.3.4/32" \
       --src-ip-ranges=1.2.3.4/32
  """

  SECURITY_POLICY_ARG = None

  _support_redirect = True
  _support_rate_limit = True
  _support_multiple_rate_limit_keys = False
  _support_header_action = True
  _support_tcl_ssl = False
  _support_fairshare = False
  _support_regional_security_policy = False

  @classmethod
  def Args(cls, parser):
    UpdateHelper.Args(
        parser,
        support_redirect=cls._support_redirect,
        support_rate_limit=cls._support_rate_limit,
        support_header_action=cls._support_header_action,
        support_tcp_ssl=cls._support_tcl_ssl,
        support_fairshare=cls._support_fairshare,
        support_regional_security_policy=cls._support_regional_security_policy,
        support_multiple_rate_limit_keys=cls._support_multiple_rate_limit_keys,
    )

  def Run(self, args):
    return UpdateHelper.Run(
        self.ReleaseTrack(),
        args,
        self._support_redirect,
        self._support_rate_limit,
        self._support_header_action,
        self._support_fairshare,
        self._support_regional_security_policy,
        self._support_multiple_rate_limit_keys,
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(base.UpdateCommand):
  r"""Update a Compute Engine security policy rule.

  *{command}* is used to update security policy rules.

  ## EXAMPLES

  To update the description and IP ranges of a rule at priority
  1000, run:

    $ {command} 1000 \
       --security-policy=my-policy \
       --description="block 1.2.3.4/32" \
       --src-ip-ranges=1.2.3.4/32
  """

  SECURITY_POLICY_ARG = None

  _support_redirect = True
  _support_rate_limit = True
  _support_multiple_rate_limit_keys = True
  _support_header_action = True
  _support_tcl_ssl = False
  _support_fairshare = False
  _support_regional_security_policy = False

  @classmethod
  def Args(cls, parser):
    UpdateHelper.Args(
        parser,
        support_redirect=cls._support_redirect,
        support_rate_limit=cls._support_rate_limit,
        support_header_action=cls._support_header_action,
        support_tcp_ssl=cls._support_tcl_ssl,
        support_fairshare=cls._support_fairshare,
        support_regional_security_policy=cls._support_regional_security_policy,
        support_multiple_rate_limit_keys=cls._support_multiple_rate_limit_keys,
    )

  def Run(self, args):
    return UpdateHelper.Run(
        self.ReleaseTrack(),
        args,
        self._support_redirect,
        self._support_rate_limit,
        self._support_header_action,
        self._support_fairshare,
        self._support_regional_security_policy,
        self._support_multiple_rate_limit_keys,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(base.UpdateCommand):
  r"""Update a Compute Engine security policy rule.

  *{command}* is used to update security policy rules.

  ## EXAMPLES

  To update the description and IP ranges of a rule at priority
  1000, run:

    $ {command} 1000 \
       --security-policy=my-policy \
       --description="block 1.2.3.4/32" \
       --src-ip-ranges=1.2.3.4/32
  """

  SECURITY_POLICY_ARG = None

  _support_redirect = True
  _support_rate_limit = True
  _support_multiple_rate_limit_keys = True
  _support_header_action = True
  _support_tcl_ssl = True
  _support_fairshare = True
  _support_regional_security_policy = True

  @classmethod
  def Args(cls, parser):
    UpdateHelper.Args(
        parser,
        support_redirect=cls._support_redirect,
        support_rate_limit=cls._support_rate_limit,
        support_header_action=cls._support_header_action,
        support_tcp_ssl=cls._support_tcl_ssl,
        support_fairshare=cls._support_fairshare,
        support_regional_security_policy=cls._support_regional_security_policy,
        support_multiple_rate_limit_keys=cls._support_multiple_rate_limit_keys,
    )

  def Run(self, args):
    return UpdateHelper.Run(
        self.ReleaseTrack(),
        args,
        self._support_redirect,
        self._support_rate_limit,
        self._support_header_action,
        self._support_fairshare,
        self._support_regional_security_policy,
        self._support_multiple_rate_limit_keys,
    )
