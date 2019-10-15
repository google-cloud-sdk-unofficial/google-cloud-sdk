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
from googlecloudsdk.api_lib.orgpolicy import utils as org_policy_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.org_policies import arguments
from googlecloudsdk.command_lib.org_policies import utils


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  r"""List the policies set on a resource.

  Lists the policies set on a resource.

  ## EXAMPLES

  To list the policies set on the project `foo-project`, run:

    $ {command} --project=foo-project
  """

  @staticmethod
  def Args(parser):
    arguments.AddResourceFlagsToParser(parser)
    parser.add_argument(
        '--show-unset',
        action='store_true',
        help='Show all available constraints for the resource.')

    parser.display_info.AddFormat('table(name, etag, updateTime)')

  def Run(self, args):
    policy_service = org_policy_service.PolicyService()
    constraint_service = org_policy_service.ConstraintService()
    org_policy_messages = org_policy_service.OrgPolicyMessages()

    parent = utils.GetResourceFromArgs(args)

    list_policies_request = org_policy_messages.OrgpolicyPoliciesListRequest(
        parent=parent)
    list_policies_response = policy_service.List(list_policies_request)
    policies = list_policies_response.policies

    if args.show_unset:
      list_constraints_request = org_policy_messages.OrgpolicyConstraintsListRequest(
          parent=parent)
      list_constraints_response = constraint_service.List(
          list_constraints_request)
      constraints = list_constraints_response.constraints

      existing_policy_names = {policy.name for policy in policies}
      for constraint in constraints:
        policy_name = org_policy_utils.GetPolicyNameFromConstraintName(
            constraint.name)
        if policy_name not in existing_policy_names:
          stubbed_policy = org_policy_messages.GoogleCloudOrgpolicyV2alpha1Policy(
              name=policy_name)
          policies.append(stubbed_policy)

    return policies
