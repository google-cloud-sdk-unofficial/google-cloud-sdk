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
"""Update Secure Source Manager branch rule command."""

from googlecloudsdk.api_lib.securesourcemanager import branch_rules
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.source_manager import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis.securesourcemanager.v1 import securesourcemanager_v1_messages

DETAILED_HELP = {
    'DESCRIPTION': (
        """
          Update a Secure Source Manager branch rule.
        """
    ),
    'EXAMPLES': (
        """
            To disable a branch rule called ``my-rule'' in repository ``my-repo'' and location ``us-central1'', run the following command:

            $ {command} my-rule --repository=my-repo --region=us-central1 --disabled
        """
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.RegionalEndpointsSupported
@base.Hidden
class Update(base.UpdateCommand):
  """Update a Secure Source Manager branch rule."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.ASYNC_FLAG.AddToParser(parser)
    resource_args.AddBranchRuleResourceArg(parser, 'to update')
    parser.add_argument(
        '--include-pattern',
        required=False,
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
        action=arg_parsers.StoreTrueFalseAction,
        required=False,
        help='Determines if a pull request is required.',
    )
    parser.add_argument(
        '--require-comments-resolved',
        action=arg_parsers.StoreTrueFalseAction,
        required=False,
        help='Determines if comments must be resolved.',
    )
    parser.add_argument(
        '--require-code-owner-approval',
        action=arg_parsers.StoreTrueFalseAction,
        required=False,
        help='Determines if code owners must approve.',
    )
    parser.add_argument(
        '--require-linear-history',
        action=arg_parsers.StoreTrueFalseAction,
        required=False,
        help='Requires linear history.',
    )
    parser.add_argument(
        '--allow-stale-reviews',
        action=arg_parsers.StoreTrueFalseAction,
        required=False,
        help='Allows stale reviews or approvals.',
    )
    parser.add_argument(
        '--disabled',
        action=arg_parsers.StoreTrueFalseAction,
        required=False,
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

    update_mask = []
    if args.IsSpecified('include_pattern'):
      update_mask.append('includePattern')
    if args.IsSpecified('minimum_approvals_count'):
      update_mask.append('minimumApprovalsCount')
    if args.IsSpecified('minimum_reviews_count'):
      update_mask.append('minimumReviewsCount')
    if args.IsSpecified('require_pull_request'):
      update_mask.append('requirePullRequest')
    if args.IsSpecified('require_comments_resolved'):
      update_mask.append('requireCommentsResolved')
    if args.IsSpecified('require_code_owner_approval'):
      update_mask.append('requireCodeOwnerApproval')
    if args.IsSpecified('require_linear_history'):
      update_mask.append('requireLinearHistory')
    if args.IsSpecified('allow_stale_reviews'):
      update_mask.append('allowStaleReviews')
    if args.IsSpecified('disabled'):
      update_mask.append('disabled')

    if not update_mask:
      raise exceptions.MinimumArgumentException(
          [
              '--include-pattern',
              '--minimum-approvals-count',
              '--minimum-reviews-count',
              '--require-pull-request',
              '--require-comments-resolved',
              '--require-code-owner-approval',
              '--require-linear-history',
              '--allow-stale-reviews',
              '--disabled',
          ],
          'At least one argument is required.',
      )

    update_operation = client.Update(
        branch_rule_ref,
        include_pattern=args.include_pattern,
        minimum_approvals_count=args.minimum_approvals_count,
        minimum_reviews_count=args.minimum_reviews_count,
        require_pull_request=args.require_pull_request,
        require_comments_resolved=args.require_comments_resolved,
        require_code_owner_approval=args.require_code_owner_approval,
        require_linear_history=args.require_linear_history,
        allow_stale_reviews=args.allow_stale_reviews,
        disabled=args.disabled,
        update_mask=update_mask,
    )

    if args.async_:
      log.UpdatedResource(branch_rule_ref.RelativeName(), is_async=True)
      return update_operation

    response = client.GetOperationResult(
        update_operation, 'Waiting for branch rule to be updated'
    )
    log.UpdatedResource(branch_rule_ref.RelativeName())
    return response


Update.detailed_help = DETAILED_HELP
