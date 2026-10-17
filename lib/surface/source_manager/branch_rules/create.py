# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Create Secure Source Manager branch rule command."""

from googlecloudsdk.api_lib.securesourcemanager import branch_rules
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.source_manager import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis.securesourcemanager.v1 import securesourcemanager_v1_messages

DETAILED_HELP = {
    'DESCRIPTION': """
          Create a Secure Source Manager branch rule.
        """,
    'EXAMPLES': """
            To create a branch rule called ``my-rule'' in repository ``my-repo'' in location ``us-central1'' protecting the main branch with pull request requirement, run the following command:

            $ {command} my-rule --repository=my-repo --region=us-central1 --include-pattern=main --require-pull-request
        """,
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.RegionalEndpointsSupported
@base.Hidden
class Create(base.CreateCommand):
  """Create a Secure Source Manager branch rule."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.ASYNC_FLAG.AddToParser(parser)
    resource_args.AddBranchRuleResourceArg(parser, 'to create')
    parser.add_argument(
        '--include-pattern',
        required=True,
        help='The pattern of the branch that can match to this branch rule.',
    )
    parser.add_argument(
        '--minimum-approvals-count',
        type=int,
        help='The minimum number of approvals required.',
    )
    parser.add_argument(
        '--minimum-reviews-count',
        type=int,
        help='The minimum number of reviews required.',
    )
    parser.add_argument(
        '--require-pull-request',
        action='store_true',
        help='Determines if a pull request is required.',
    )
    parser.add_argument(
        '--require-comments-resolved',
        action='store_true',
        help='Determines if comments must be resolved.',
    )
    parser.add_argument(
        '--require-code-owner-approval',
        action='store_true',
        help='Determines if code owners must approve.',
    )
    parser.add_argument(
        '--require-linear-history',
        action='store_true',
        help='Requires linear history.',
    )
    parser.add_argument(
        '--allow-stale-reviews',
        action='store_true',
        help='Allows stale reviews or approvals.',
    )
    parser.add_argument(
        '--disabled',
        action='store_true',
        help='Determines if the branch rule is disabled.',
    )

  def Run(
      self, args: parser_extensions.Namespace
  ) -> (
      securesourcemanager_v1_messages.Operation
      | securesourcemanager_v1_messages.Operation.ResponseValue
      | securesourcemanager_v1_messages.BranchRule
      | None
  ):
    branch_rule_ref = args.CONCEPTS.branch_rule.Parse()
    client = branch_rules.BranchRulesClient(
        location=branch_rule_ref.locationsId
    )

    create_operation = client.Create(
        branch_rule_ref,
        args.include_pattern,
        args.minimum_approvals_count,
        args.minimum_reviews_count,
        args.require_pull_request,
        args.require_comments_resolved,
        args.require_code_owner_approval,
        args.require_linear_history,
        args.allow_stale_reviews,
        args.disabled,
    )

    if args.async_:
      log.CreatedResource(branch_rule_ref.RelativeName(), is_async=True)
      return create_operation

    response = client.GetOperationResult(
        create_operation, 'Waiting for branch rule to be created'
    )
    log.CreatedResource(branch_rule_ref.RelativeName())
    return response


Create.detailed_help = DETAILED_HELP
