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

"""Command for deleting security policies rules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute.security_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.security_policies import flags as security_policies_flags
from googlecloudsdk.command_lib.compute.security_policies.rules import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class DeleteHelper(object):
  r"""Delete Compute Engine security policy rules.

  *{command}* is used to delete security policy rules.

  ## EXAMPLES

  To delete the rule at priority 1000, run:

    $ {command} 1000 \
       --security-policy=my-policy
  """

  SECURITY_POLICY_ARG = None
  NAME_ARG = None

  @classmethod
  def Args(cls, parser, support_regional_security_policy, support_net_lb):
    """Generates the flagset for a Delete command."""
    if support_regional_security_policy or support_net_lb:
      cls.NAME_ARG = (flags.PriorityArgument('delete', is_plural=True))
      cls.NAME_ARG.AddArgument(
          parser, operation_type='delete', cust_metavar='PRIORITY')
      flags.AddRegionFlag(parser, 'delete')
      cls.SECURITY_POLICY_ARG = (
          security_policies_flags.SecurityPolicyMultiScopeArgumentForRules()
      )
    else:
      flags.AddPriority(parser, 'delete', is_plural=True)
      cls.SECURITY_POLICY_ARG = (
          security_policies_flags.SecurityPolicyArgumentForRules()
      )
    cls.SECURITY_POLICY_ARG.AddArgument(parser)
    parser.display_info.AddCacheUpdater(
        security_policies_flags.SecurityPoliciesCompleter
    )

  @classmethod
  def Run(
      cls, release_track, args, support_regional_security_policy, support_net_lb
  ):
    """Validates arguments and deletes security policy rule(s)."""
    holder = base_classes.ComputeApiHolder(release_track)
    refs = []
    if support_regional_security_policy or support_net_lb:
      if args.security_policy:
        security_policy_ref = cls.SECURITY_POLICY_ARG.ResolveAsResource(
            args,
            holder.resources,
            default_scope=compute_scope.ScopeEnum.GLOBAL)
        if getattr(security_policy_ref, 'region', None) is not None:
          for name in args.names:
            refs.append(holder.resources.Parse(
                name,
                collection='compute.regionSecurityPolicyRules',
                params={
                    'project': properties.VALUES.core.project.GetOrFail,
                    'region': security_policy_ref.region,
                    'securityPolicy': args.security_policy,
                }))
        else:
          for name in args.names:
            refs.append(holder.resources.Parse(
                name,
                collection='compute.securityPolicyRules',
                params={
                    'project': properties.VALUES.core.project.GetOrFail,
                    'securityPolicy': args.security_policy,
                },
            ))
      else:
        for name in args.names:
          try:
            refs.append(holder.resources.Parse(
                name,
                collection='compute.regionSecurityPolicyRules',
                params={
                    'project': properties.VALUES.core.project.GetOrFail,
                    'region': getattr(args, 'region', None),
                },
            ))
          except (
              resources.RequiredFieldOmittedException,
              resources.WrongResourceCollectionException,
          ):
            refs.append(holder.resources.Parse(
                name,
                collection='compute.securityPolicyRules',
                params={
                    'project': properties.VALUES.core.project.GetOrFail,
                },
            ))
    else:
      for name in args.names:
        refs.append(holder.resources.Parse(
            name,
            collection='compute.securityPolicyRules',
            params={
                'project': properties.VALUES.core.project.GetOrFail,
                'securityPolicy': args.security_policy
            }))
    utils.PromptForDeletion(refs)

    requests = []
    for ref in refs:
      security_policy_rule = client.SecurityPolicyRule(
          ref, compute_client=holder.client)
      requests.extend(security_policy_rule.Delete(only_generate_request=True))

    return holder.client.MakeRequests(requests)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class DescribeGA(base.DeleteCommand):
  r"""Delete Compute Engine security policy rules.

  *{command}* is used to delete security policy rules.

  ## EXAMPLES

  To delete the rule at priority 1000, run:

    $ {command} 1000 \
       --security-policy=my-policy
  """

  SECURITY_POLICY_ARG = None

  _support_regional_security_policy = False
  _support_net_lb = False

  @classmethod
  def Args(cls, parser):
    DeleteHelper.Args(
        parser,
        support_regional_security_policy=cls._support_regional_security_policy,
        support_net_lb=cls._support_net_lb)

  def Run(self, args):
    return DeleteHelper.Run(
        self.ReleaseTrack(),
        args,
        support_regional_security_policy=self._support_regional_security_policy,
        support_net_lb=self._support_net_lb)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(base.DeleteCommand):
  r"""Delete Compute Engine security policy rules.

  *{command}* is used to delete security policy rules.

  ## EXAMPLES

  To delete the rule at priority 1000, run:

    $ {command} 1000 \
       --security-policy=my-policy
  """

  SECURITY_POLICY_ARG = None

  _support_regional_security_policy = True
  _support_net_lb = True

  @classmethod
  def Args(cls, parser):
    DeleteHelper.Args(
        parser,
        support_regional_security_policy=cls._support_regional_security_policy,
        support_net_lb=cls._support_net_lb)

  def Run(self, args):
    return DeleteHelper.Run(
        self.ReleaseTrack(),
        args,
        support_regional_security_policy=self._support_regional_security_policy,
        support_net_lb=self._support_net_lb)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeleteAlpha(base.DeleteCommand):
  r"""Delete Compute Engine security policy rules.

  *{command}* is used to delete security policy rules.

  ## EXAMPLES

  To delete the rule at priority 1000, run:

    $ {command} 1000 \
       --security-policy=my-policy
  """

  SECURITY_POLICY_ARG = None

  _support_regional_security_policy = True
  _support_net_lb = True

  @classmethod
  def Args(cls, parser):
    DeleteHelper.Args(
        parser,
        support_regional_security_policy=cls._support_regional_security_policy,
        support_net_lb=cls._support_net_lb)

  def Run(self, args):
    return DeleteHelper.Run(
        self.ReleaseTrack(),
        args,
        support_regional_security_policy=self._support_regional_security_policy,
        support_net_lb=self._support_net_lb)
