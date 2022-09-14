# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command for removing exclusions for preconfigured WAF rule evaluation from security policy rules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.security_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.security_policies import flags as security_policy_flags
from googlecloudsdk.command_lib.compute.security_policies.rules import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class RemovePreconfigWafExclusion(base.UpdateCommand):
  r"""Remove an exclusion configuration for preconfigured WAF evaluation from a security policy rule.

  *{command}* is used to remove an exclusion configuration for preconfigured WAF
  evaluation from a security policy rule.

  Note that request field exclusions are associated with a target, which can be
  a single rule set, or a rule set plus a list of rule IDs under the rule set.

  It is possible to remove request field exclusions at 3 levels:
  - Remove specific request field exclusions that are associated with a matching
    target.
  - Remove all the request field exclusions that are associated with a matching
    target.
  - Remove all the request field exclusions that are configured under the
    security policy rule, regardless of the target.

  ## EXAMPLES

  To remove specific request field exclusions that are associated with the
  target of 'sqli-stable': ['owasp-crs-v030001-id942110-sqli',
  'owasp-crs-v030001-id942120-sqli'], run:

    $ {command} 1000 \
       --security-policy=my-policy \
       --target-rule-set=sqli-stable \
       --target-rule-ids=owasp-crs-v030001-id942110-sqli,owasp-crs-v030001-id942120-sqli
       \
       --request-header-to-exclude=op=EQUALS,val=abc \
       --request-header-to-exclude=op=STARTS_WITH,val=xyz \
       --request-uri-to-exclude=op=EQUALS_ANY

  To remove all the request field exclusions that are associated with the target
  of 'sqli-stable': ['owasp-crs-v030001-id942110-sqli',
  'owasp-crs-v030001-id942120-sqli'], run:

    $ {command} 1000 \
       --security-policy=my-policy \
       --target-rule-set=sqli-stable \
       --target-rule-ids=owasp-crs-v030001-id942110-sqli,owasp-crs-v030001-id942120-sqli

  To remove all the request field exclusions that are associated with the target
  of 'sqli-stable': [], run:

    $ {command} 1000 \
       --security-policy=my-policy \
       --target-rule-set=sqli-stable

  To remove all the request field exclusions that are configured under the
  security policy rule, regardless of the target, run:

    $ {command} 1000 \
       --security-policy=my-policy \
       --target-rule-set=*
  """

  @classmethod
  def Args(cls, parser):
    """Generates the flagset for a RemovePreconfigWafExclusion command."""
    flags.AddPriority(
        parser,
        'remove the exclusion configuration for preconfigured WAF evaluation')
    cls.SECURITY_POLICY_ARG = (
        security_policy_flags.SecurityPolicyArgumentForRules())
    cls.SECURITY_POLICY_ARG.AddArgument(parser)
    flags.AddTargetRuleSet(parser=parser, is_add=False)
    flags.AddTargetRuleIds(parser=parser, is_add=False)
    flags.AddRequestHeader(parser=parser, is_add=False)
    flags.AddRequestCookie(parser=parser, is_add=False)
    flags.AddRequestQueryParam(parser=parser, is_add=False)
    flags.AddRequestUri(parser=parser, is_add=False)

  def _IsIdenticalTarget(self,
                         existing_exclusion,
                         target_rule_set,
                         target_rule_ids=None):
    return target_rule_set == existing_exclusion.targetRuleSet and set(
        target_rule_ids) == set(existing_exclusion.targetRuleIds)

  def _ConvertRequestFieldToAdd(self, compute_client, request_field_to_remove):
    request_field = (
        compute_client.messages
        .SecurityPolicyRulePreconfiguredWafConfigExclusionFieldParams())

    op = request_field_to_remove.get('op') or ''
    if op:
      request_field.op = (
          compute_client.messages
          .SecurityPolicyRulePreconfiguredWafConfigExclusionFieldParams
          .OpValueValuesEnum(op))

    val = request_field_to_remove.get('val') or ''
    if val:
      request_field.val = val

    return request_field

  def _RemoveRequestFields(self, existing_request_fields,
                           request_fields_to_remove):
    new_request_fields = []
    for existing_request_field in existing_request_fields:
      if existing_request_field not in request_fields_to_remove:
        new_request_fields.append(existing_request_field)
    return new_request_fields

  def _UpdateExclusion(self,
                       compute_client,
                       existing_exclusion,
                       request_headers=None,
                       request_cookies=None,
                       request_query_params=None,
                       request_uris=None):
    new_exclusion = (
        compute_client.messages
        .SecurityPolicyRulePreconfiguredWafConfigExclusion())
    new_exclusion.targetRuleSet = existing_exclusion.targetRuleSet
    for target_rule_id in existing_exclusion.targetRuleIds or []:
      new_exclusion.targetRuleIds.append(target_rule_id)

    request_headers_to_remove = []
    for request_header in request_headers or []:
      request_headers_to_remove.append(
          self._ConvertRequestFieldToAdd(compute_client, request_header))
    new_exclusion.requestHeadersToExclude.extend(
        self._RemoveRequestFields(existing_exclusion.requestHeadersToExclude,
                                  request_headers_to_remove))

    request_cookies_to_remove = []
    for request_cookie in request_cookies or []:
      request_cookies_to_remove.append(
          self._ConvertRequestFieldToAdd(compute_client, request_cookie))
    new_exclusion.requestCookiesToExclude.extend(
        self._RemoveRequestFields(existing_exclusion.requestCookiesToExclude,
                                  request_cookies_to_remove))

    request_query_params_to_remove = []
    for request_query_param in request_query_params or []:
      request_query_params_to_remove.append(
          self._ConvertRequestFieldToAdd(compute_client, request_query_param))
    new_exclusion.requestQueryParamsToExclude.extend(
        self._RemoveRequestFields(
            existing_exclusion.requestQueryParamsToExclude,
            request_query_params_to_remove))

    request_uris_to_remove = []
    for request_uri in request_uris or []:
      request_uris_to_remove.append(
          self._ConvertRequestFieldToAdd(compute_client, request_uri))
    new_exclusion.requestUrisToExclude.extend(
        self._RemoveRequestFields(existing_exclusion.requestUrisToExclude,
                                  request_uris_to_remove))

    if not (new_exclusion.requestHeadersToExclude or
            new_exclusion.requestCookiesToExclude or
            new_exclusion.requestQueryParamsToExclude or
            new_exclusion.requestUrisToExclude):
      return None
    return new_exclusion

  def _UpdatePreconfigWafConfig(self, compute_client, existing_rule, args):
    new_preconfig_waf_config = (
        compute_client.messages.SecurityPolicyRulePreconfiguredWafConfig())
    if args.target_rule_set == '*':
      return new_preconfig_waf_config

    has_request_field_args = False
    if (args.IsSpecified('request_header_to_exclude') or
        args.IsSpecified('request_cookie_to_exclude') or
        args.IsSpecified('request_query_param_to_exclude') or
        args.IsSpecified('request_uri_to_exclude')):
      has_request_field_args = True

    if existing_rule.preconfiguredWafConfig:
      exclusions = existing_rule.preconfiguredWafConfig.exclusions
    else:
      exclusions = []

    for exclusion in exclusions:
      if self._IsIdenticalTarget(exclusion, args.target_rule_set,
                                 args.target_rule_ids or []):
        if has_request_field_args:
          new_exclusion = self._UpdateExclusion(
              compute_client, exclusion, args.request_header_to_exclude,
              args.request_cookie_to_exclude,
              args.request_query_param_to_exclude, args.request_uri_to_exclude)
          if new_exclusion:
            new_preconfig_waf_config.exclusions.append(new_exclusion)
      else:
        new_preconfig_waf_config.exclusions.append(exclusion)

    return new_preconfig_waf_config

  def Run(self, args):
    """Validates arguments and patches a security policy rule."""
    if args.target_rule_set == '*':
      if (args.IsSpecified('target_rule_ids') or
          args.IsSpecified('request_header_to_exclude') or
          args.IsSpecified('request_cookie_to_exclude') or
          args.IsSpecified('request_query_param_to_exclude') or
          args.IsSpecified('request_uri_to_exclude')):
        raise exceptions.InvalidArgumentException(
            'target-rule-set',
            'Arguments in [--target-rule-ids, --request-header-to-exclude, '
            '--request-cookie-to-exclude, --request-query-param-to-exclude, '
            '--request-uri-to-exclude] cannot be specified when '
            '--target-rule-set is set to *.')

    for request_fields in [
        args.request_header_to_exclude or [], args.request_cookie_to_exclude or
        [], args.request_query_param_to_exclude or [],
        args.request_uri_to_exclude or []
    ]:
      for request_field in request_fields:
        op = request_field.get('op') or ''
        if not op or op not in [
            'EQUALS', 'STARTS_WITH', 'ENDS_WITH', 'CONTAINS', 'EQUALS_ANY'
        ]:
          raise exceptions.InvalidArgumentException(
              'op',
              'A request field operator must be one of [EQUALS, STARTS_WITH, '
              'ENDS_WITH, CONTAINS, EQUALS_ANY].')

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    compute_client = holder.client
    ref = holder.resources.Parse(
        args.name,
        collection='compute.securityPolicyRules',
        params={
            'project': properties.VALUES.core.project.GetOrFail,
            'securityPolicy': args.security_policy
        })
    security_policy_rule = client.SecurityPolicyRule(
        ref, compute_client=compute_client)
    existing_rule = security_policy_rule.Describe()[0]

    new_preconfig_waf_config = self._UpdatePreconfigWafConfig(
        compute_client, existing_rule, args)
    return security_policy_rule.Patch(
        preconfig_waf_config=new_preconfig_waf_config)
