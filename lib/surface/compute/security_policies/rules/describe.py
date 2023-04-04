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

"""Command for describing security policies rules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.security_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.security_policies import flags as security_policy_flags
from googlecloudsdk.command_lib.compute.security_policies.rules import flags
from googlecloudsdk.core import properties


class DescribeHelper(object):
  r"""Describe a Compute Engine security policy rule.

  *{command}* displays all data associated with a security policy rule.

  ## EXAMPLES

  To describe the rule at priority 1000, run:

    $ {command} 1000 \
       --security-policy=my-policy
  """

  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser, support_regional_security_policy, support_net_lb):
    """Generates the flagset for a Describe command."""
    flags.AddPriority(parser, 'describe')
    if support_regional_security_policy or support_net_lb:
      flags.AddRegionFlag(parser, 'describe')
      cls.SECURITY_POLICY_ARG = (
          security_policy_flags.SecurityPolicyMultiScopeArgumentForRules()
      )
    else:
      cls.SECURITY_POLICY_ARG = (
          security_policy_flags.SecurityPolicyArgumentForRules()
      )
    cls.SECURITY_POLICY_ARG.AddArgument(parser)

  @classmethod
  def Run(
      cls, release_track, args, support_regional_security_policy, support_net_lb
  ):
    """Validates arguments and describes a security policy rule."""
    holder = base_classes.ComputeApiHolder(release_track)
    ref = None
    if support_regional_security_policy or support_net_lb:
      security_policy_ref = cls.SECURITY_POLICY_ARG.ResolveAsResource(
          args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL
      )
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
                'securityPolicy': args.security_policy
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

    return security_policy_rule.Describe()


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class DescribeGABeta(base.DescribeCommand):
  r"""Describe a Compute Engine security policy rule.

  *{command}* displays all data associated with a security policy rule.

  ## EXAMPLES

  To describe the rule at priority 1000, run:

    $ {command} 1000 \
       --security-policy=my-policy
  """

  SECURITY_POLICY_ARG = None

  _support_regional_security_policy = False
  _support_net_lb = False

  @classmethod
  def Args(cls, parser):
    DescribeHelper.Args(
        parser,
        support_regional_security_policy=cls._support_regional_security_policy,
        support_net_lb=cls._support_net_lb)

  def Run(self, args):
    return DescribeHelper.Run(
        self.ReleaseTrack(),
        args,
        support_regional_security_policy=self._support_regional_security_policy,
        support_net_lb=self._support_net_lb)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(base.DescribeCommand):
  r"""Describe a Compute Engine security policy rule.

  *{command}* displays all data associated with a security policy rule.

  ## EXAMPLES

  To describe the rule at priority 1000, run:

    $ {command} 1000 \
       --security-policy=my-policy
  """

  SECURITY_POLICY_ARG = None

  _support_regional_security_policy = True
  _support_net_lb = True

  @classmethod
  def Args(cls, parser):
    DescribeHelper.Args(
        parser,
        support_regional_security_policy=cls._support_regional_security_policy,
        support_net_lb=cls._support_net_lb)

  def Run(self, args):
    return DescribeHelper.Run(
        self.ReleaseTrack(),
        args,
        support_regional_security_policy=self._support_regional_security_policy,
        support_net_lb=self._support_net_lb)
