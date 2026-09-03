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
"""Creates a Backup and DR AutoProtectionPolicy."""

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.backupdr import auto_protection_policies
from googlecloudsdk.api_lib.backupdr import util
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.backupdr import flags
from googlecloudsdk.core import log

AutoProtectionPoliciesClient = (
    auto_protection_policies.AutoProtectionPoliciesClient
)


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.Hidden
class Create(base.CreateCommand):
  """Create a Backup and DR AutoProtectionPolicy."""

  detailed_help = {
      'BRIEF': 'Create a Backup and DR AutoProtectionPolicy.',
      'DESCRIPTION': 'Create a Backup and DR AutoProtectionPolicy.',
      'EXAMPLES': """\
        To create an AutoProtectionPolicy 'my-policy' in 'us-central1' with a criteria label, run:

          # gcloud-disable-gdu-domain
          $ {command} my-policy --location=us-central1 --criteria=key=environment,value=prod --description="My Policy" --backup-plan-details="resource-type=compute.googleapis.com/Instance,backup-plan=projects/my-proj/locations/us-central1/backupPlans/my-plan"
      """,
  }

  @classmethod
  def Args(cls, parser):
    """Specifies additional command flags."""
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)

    flags.AddAutoProtectionPolicyResourceArg(
        parser,
        'Name of the AutoProtectionPolicy to create.',
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
        required=True,
        help='Criteria of the policy in format key=VALUE,value=VALUE.',
    )

    parser.add_argument(
        '--backup-plan-details',
        action='append',
        required=True,
        type=arg_parsers.ArgDict(
            spec={'resource-type': str, 'backup-plan': str},
            required_keys=['resource-type', 'backup-plan']
        ),
        help=(
            'Backup plan details in format '
            'resource-type=VALUE,backup-plan=VALUE. This flag can be repeated '
            'to specify multiple backup plans.'
        ),
    )

  def Run(self, args):
    """Constructs and sends request."""
    api_version = util.GetApiVersion(self.ReleaseTrack())
    client = AutoProtectionPoliciesClient(api_version=api_version)
    policy_ref = args.CONCEPTS.auto_protection_policy.Parse()

    try:
      operation = client.Create(
          resource=policy_ref,
          description=args.description,
          criteria_label=args.criteria,
          backup_plan_details=args.backup_plan_details,
      )
    except apitools_exceptions.HttpError as e:
      raise exceptions.HttpException(e, util.HTTP_ERROR_FORMAT)

    if args.async_:
      log.CreatedResource(
          policy_ref.RelativeName(),
          kind='auto protection policy',
          is_async=True,
          details=util.ASYNC_OPERATION_MESSAGE.format(operation.name),
      )
      return operation

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=(
            'Creating auto protection policy [{}]. (This operation could take'
            ' up to 2 minutes.)'.format(policy_ref.RelativeName())
        ),
    )
    log.CreatedResource(
        policy_ref.RelativeName(), kind='auto protection policy'
    )
    return resource
