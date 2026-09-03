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
"""Updates a Backup and DR AutoProtectionPolicy."""

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.backupdr import auto_protection_policies
from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.backupdr import flags
from googlecloudsdk.core import log

AutoProtectionPoliciesClient = (
    auto_protection_policies.AutoProtectionPoliciesClient
)


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.Hidden
class Update(base.UpdateCommand):
  """Update a Backup and DR AutoProtectionPolicy."""

  detailed_help = {
      'BRIEF': 'Update a Backup and DR AutoProtectionPolicy.',
      'DESCRIPTION': 'Update a Backup and DR AutoProtectionPolicy.',
      'EXAMPLES': """\
        To update the description of an AutoProtectionPolicy 'my-policy' in 'us-central1', run:

          $ {command} my-policy --location=us-central1 --description="Updated Policy"
      """,
  }

  @classmethod
  def Args(cls, parser):
    """Specifies additional command flags."""
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)

    flags.AddAutoProtectionPolicyResourceArg(
        parser,
        'Name of the AutoProtectionPolicy to update.',
    )

    parser.add_argument(
        '--description',
        help='Description for the policy.',
    )

    parser.add_argument(
        '--criteria',
        type=arg_parsers.ArgDict(
            spec={'key': str, 'value': str}, required_keys=['key', 'value']
        ),
        required=False,
        help='Criteria of the policy in format key=VALUE,value=VALUE.',
    )

    parser.add_argument(
        '--backup-plan-details',
        action='append',
        type=arg_parsers.ArgDict(
            spec={'resource-type': str, 'backup-plan': str},
            required_keys=['resource-type', 'backup-plan']
        ),
        help=(
            'Backup plan details in format '
            'resource-type=VALUE,backup-plan=VALUE.'
        ),
    )

  def Run(self, args):
    """Constructs and sends request."""
    has_desc = args.IsSpecified('description')
    has_criteria = args.IsSpecified('criteria')
    has_details = args.IsSpecified('backup_plan_details')

    if not (has_desc or has_criteria or has_details):
      raise calliope_exceptions.MinimumArgumentException(
          [
              '--description',
              '--criteria',
              '--backup-plan-details',
          ],
          'Please specify at least one property to update'
      )

    api_version = util.GetApiVersion(self.ReleaseTrack())
    client = AutoProtectionPoliciesClient(api_version=api_version)
    policy_ref = args.CONCEPTS.auto_protection_policy.Parse()

    description = args.description if args.IsSpecified('description') else None
    criteria_label = args.criteria if args.IsSpecified('criteria') else None
    backup_plan_details = (
        args.backup_plan_details
        if args.IsSpecified('backup_plan_details')
        else None
    )

    try:
      operation = client.Patch(
          resource=policy_ref,
          description=description,
          criteria_label=criteria_label,
          backup_plan_details=backup_plan_details,
      )
    except apitools_exceptions.HttpError as e:
      raise exceptions.HttpException(e, util.HTTP_ERROR_FORMAT)

    if args.async_:
      log.UpdatedResource(
          policy_ref.RelativeName(),
          kind='auto protection policy',
          is_async=True,
          details=util.ASYNC_OPERATION_MESSAGE.format(operation.name),
      )
      return operation

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=(
            f'Updating auto protection policy [{policy_ref.RelativeName()}].'
            ' (This operation could take up to 2 minutes.)'
        ),
    )
    log.UpdatedResource(
        policy_ref.RelativeName(), kind='auto protection policy'
    )
    return resource
