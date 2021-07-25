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
"""gcloud dns response-policies rules create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.command_lib.dns import resource_args
from googlecloudsdk.command_lib.dns import util as command_util
from googlecloudsdk.core import log


def _AddArgsCommon(parser, messages):
  """Adds the common arguments for all versions."""
  flags.GetLocalDataResourceRecordSets().AddToParser(parser)
  flags.AddResponsePolicyRulesBehaviorFlagArgs(parser, messages)

  parser.add_argument(
      '--dns-name',
      required=True,
      help='DNS name (wildcard or exact) to apply this rule to.')


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(base.UpdateCommand):
  r"""Creates a new Cloud DNS response policy rule.

      This command creates a new Cloud DNS response policy rule.

      ## EXAMPLES

      To create a new response policy rule with local data rrsets, run:

        $ {command} myresponsepolicyrule --response-policy="myresponsepolicy" --dns-name="www.zone.com." --local-data=name=www.zone.com.,type=CNAME,ttl=21600,rrdatas=zone.com.

      To create a new response policy rule with behavior, run:

        $ {command} myresponsepolicyrule --response-policy="myresponsepolicy" --dns-name="www.zone.com." --behavior=bypassResponsePolicy
  """

  @staticmethod
  def Args(parser):
    messages = apis.GetMessagesModule('dns', 'v1beta2')
    _AddArgsCommon(parser, messages)
    resource_args.AddResponsePolicyRuleArg(
        parser, verb='to create', api_version='v1beta2')
    parser.display_info.AddFormat('json')

  def Run(self, args):
    api_version = util.GetApiFromTrack(self.ReleaseTrack())
    client = util.GetApiClient(api_version)
    messages = apis.GetMessagesModule('dns', api_version)

    # Get Response Policy Rule
    response_policy_rule_ref = args.CONCEPTS.response_policy_rule.Parse()
    response_policy_rule_name = response_policy_rule_ref.Name()

    response_policy_rule = messages.ResponsePolicyRule(
        ruleName=response_policy_rule_name)

    response_policy_rule.dnsName = args.dns_name
    response_policy = messages.ResponsePolicy(
        responsePolicyName=args.response_policy)

    if args.IsSpecified('behavior') and args.IsSpecified('local_data'):
      raise exceptions.ConflictingArgumentsException(
          'Only one of arguments [--behavior, --local-data] is allowed.')

    if args.IsSpecified('behavior'):
      response_policy_rule.behavior = command_util\
          .ParseResponsePolicyRulesBehavior(args, api_version)
    elif args.IsSpecified('local_data'):
      rrsets = []
      for rrset in args.local_data:
        resource_record_set = messages.ResourceRecordSet(
            name=rrset.get('name'),
            type=rrset.get('type'),
            ttl=rrset.get('ttl'),
            rrdatas=rrset.get('rrdatas').split('|'))
        rrsets.append(resource_record_set)

      local_data = messages.ResponsePolicyRuleLocalData(
          localDatas=rrsets)
      response_policy_rule.localData = local_data

    create_request = messages.DnsResponsePolicyRulesCreateRequest(
        responsePolicy=response_policy.responsePolicyName,
        project=response_policy_rule_ref.project,
        responsePolicyRule=response_policy_rule)

    result = client.responsePolicyRules.Create(create_request)

    log.CreatedResource(response_policy_rule, kind='ResponsePolicyRule')

    return result


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  r"""Creates a new Cloud DNS response policy rule.

      This command creates a new Cloud DNS response policy rule.

       ## EXAMPLES

      To create a new response policy rule with local data rrsets, run:

        $ {command} myresponsepolicyrule --response-policy="myresponsepolicy" --dns-name="www.zone.com." --local-data=name=www.zone.com.,type=CNAME,ttl=21600,rrdatas=zone.com.

      To create a new response policy rule with behavior, run:

        $ {command} myresponsepolicyrule --response-policy="myresponsepolicy" --dns-name="www.zone.com." --behavior=bypassResponsePolicy
  """

  @staticmethod
  def Args(parser):
    resource_args.AddResponsePolicyRuleArg(
        parser, verb='to create', api_version='v1alpha2')
    messages = apis.GetMessagesModule('dns', 'v1alpha2')
    _AddArgsCommon(parser, messages)
    parser.display_info.AddFormat('json')
