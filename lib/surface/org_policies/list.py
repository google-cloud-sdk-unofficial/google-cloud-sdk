# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""List command for the Org Policy CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.orgpolicy import service as org_policy_service
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.org_policies import arguments
from googlecloudsdk.command_lib.org_policies import utils

DETAILED_HELP = {
    'DESCRIPTION':
        """\
      Lists the policies set on a resource.
      """,
    'EXAMPLES':
        """\
      To list the policies set on the Project 'foo-project', run:

      $ {command} --project=foo-project
      """,
}


def HasListPolicy(spec):
  if spec:
    for rule in spec.rules:
      if (rule.values is not None or rule.allowAll is not None or
          rule.denyAll is not None):
        return True
  return False


def HasBooleanPolicy(spec):
  if spec:
    return any([rule.enforce is not None for rule in spec.rules])
  return False


def HasDryRunBooleanPolicy(dry_run_spec):
  if dry_run_spec:
    return any([rule.enforce is not None for rule in dry_run_spec.rules])
  return False


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List the policies set on a resource."""

  @staticmethod
  def Args(parser):
    arguments.AddResourceFlagsToParser(parser)
    parser.add_argument(
        '--show-unset',
        action='store_true',
        help='Show all available constraints for the resource.')

    parser.display_info.AddFormat(
        'table(constraint, listPolicy, booleanPolicy, etag)')

  def Run(self, args):
    org_policy_api = org_policy_service.OrgPolicyApi(self.ReleaseTrack())
    parent = utils.GetResourceFromArgs(args)
    output = []

    policies = org_policy_api.ListPolicies(parent).policies
    for policy in policies:
      spec = policy.spec
      dry_run_spec = policy.dryRunSpec
      list_policy_set = HasListPolicy(spec)
      boolean_policy_set = HasBooleanPolicy(spec)
      dry_run_boolean_policy_set = HasDryRunBooleanPolicy(dry_run_spec)
      boolean_policy_output = '-'
      if boolean_policy_set and dry_run_boolean_policy_set:
        boolean_policy_output = 'LIVE_AND_DRY_RUN_SET'
      elif boolean_policy_set:
        boolean_policy_output = 'SET'
      elif dry_run_boolean_policy_set:
        boolean_policy_output = 'DRY_RUN_SET'
      output.append({
          'constraint': policy.name.split('/')[-1],
          'listPolicy': 'SET' if list_policy_set else '-',
          'booleanPolicy': boolean_policy_output,
          'etag': spec.etag if spec else dry_run_spec.etag
      })
    if args.show_unset:
      constraints = org_policy_api.ListConstraints(parent).constraints

      existing_policy_names = {row['constraint'] for row in output}
      for constraint in constraints:
        constraint_name = constraint.name.split('/')[-1]
        if constraint_name not in existing_policy_names:
          output.append({
              'constraint': constraint_name,
              'listPolicy': '-',
              'booleanPolicy': '-'
          })

    return output


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListALPHA(base.ListCommand):
  """List the policies set on a resource."""

  @staticmethod
  def Args(parser):
    arguments.AddResourceFlagsToParser(parser)
    parser.add_argument(
        '--show-unset',
        action='store_true',
        help='Show all available constraints for the resource.')

    parser.display_info.AddFormat(
        'table(constraint, listPolicy, booleanPolicy, etag)')

  def Run(self, args):
    org_policy_api = org_policy_service.OrgPolicyApi(self.ReleaseTrack())
    parent = utils.GetResourceFromArgs(args)
    output = []

    policies = org_policy_api.ListPolicies(parent).policies
    for policy in policies:
      spec = policy.spec
      list_policy_set = HasListPolicy(spec)
      boolean_policy_set = HasBooleanPolicy(spec)
      output.append({
          'constraint': policy.name.split('/')[-1],
          'listPolicy': 'SET' if list_policy_set else '-',
          'booleanPolicy': 'SET' if boolean_policy_set else '-',
          'etag': spec.etag
      })
    if args.show_unset:
      constraints = org_policy_api.ListConstraints(parent).constraints

      existing_policy_names = {row['constraint'] for row in output}
      for constraint in constraints:
        constraint_name = constraint.name.split('/')[-1]
        if constraint_name not in existing_policy_names:
          output.append({
              'constraint': constraint_name,
              'listPolicy': '-',
              'booleanPolicy': '-'
          })

    return output


List.detailed_help = DETAILED_HELP
ListALPHA.detailed_help = DETAILED_HELP
