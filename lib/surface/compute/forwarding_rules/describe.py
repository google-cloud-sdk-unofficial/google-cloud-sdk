# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for describing forwarding rules."""


from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.forwarding_rules import flags


def _Args(parser):
  forwarding_rules_arg = flags.ForwardingRuleArgument()
  forwarding_rules_arg.AddArgument(parser, operation_type='describe')
  return forwarding_rules_arg


def _Run(args, holder, forwarding_rules_arg):
  """Issues request necessary to describe the Forwarding Rule."""
  client = holder.client

  forwarding_rule_ref = forwarding_rules_arg.ResolveAsResource(
      args,
      holder.resources,
      scope_lister=compute_flags.GetDefaultScopeLister(client))

  request_kwargs = forwarding_rule_ref.AsDict()
  if forwarding_rule_ref.Collection() == 'compute.forwardingRules':
    service = client.apitools_client.forwardingRules
    if args.IsKnownAndSpecified('view'):
      request_kwargs['view'] = (
          client.messages.ComputeForwardingRulesGetRequest.ViewValueValuesEnum(
              args.view
          )
      )
    request = client.messages.ComputeForwardingRulesGetRequest(**request_kwargs)
  elif forwarding_rule_ref.Collection() == 'compute.globalForwardingRules':
    service = client.apitools_client.globalForwardingRules
    if args.IsKnownAndSpecified('view'):
      request_kwargs['view'] = (
          client.messages.ComputeGlobalForwardingRulesGetRequest.ViewValueValuesEnum(
              args.view
          )
      )
    request = client.messages.ComputeGlobalForwardingRulesGetRequest(
        **request_kwargs
    )

  return client.MakeRequests([(service, 'Get', request)])[0]


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.PREVIEW)
@base.UniverseCompatible
class Describe(base.DescribeCommand):
  """Display detailed information about a forwarding rule.

  *{command}* displays all data associated with a forwarding rule
  in a project.

  ## EXAMPLES
  To get details about a global forwarding rule, run:

    $ {command} FORWARDING-RULE --global

  To get details about a regional forwarding rule, run:

    $ {command} FORWARDING-RULE --region=us-central1
  """

  FORWARDING_RULE_ARG = None

  @staticmethod
  def Args(parser):
    Describe.FORWARDING_RULE_ARG = _Args(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder, self.FORWARDING_RULE_ARG)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class DescribeBeta(Describe):
  """Display detailed information about a forwarding rule.

  *{command}* displays all data associated with a forwarding rule
  in a project.

  ## EXAMPLES
  To get details about a global forwarding rule, run:

    $ {command} FORWARDING-RULE --global

  To get details about a regional forwarding rule, run:

    $ {command} FORWARDING-RULE --region=us-central1

  To get full details, including any extensions attached to the rule, run:

    $ {command} FORWARDING-RULE --region=us-central1 --view=FULL
  """

  @staticmethod
  def Args(parser):
    DescribeBeta.FORWARDING_RULE_ARG = _Args(parser)
    parser.add_argument(
        '--view',
        choices=['BASIC', 'FULL'],
        help=(
            'The view of the forwarding rule to return. '
            'BASIC includes the standard fields. '
            'FULL includes standard fields plus any '
            'extensions attached to the forwarding rule.'
        ),
    )
