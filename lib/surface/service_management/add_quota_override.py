# Copyright 2016 Google Inc. All Rights Reserved.
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

"""service-management add-quota-override command."""

import sys

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.service_management import consumers_flags
from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


class AddQuotaOverride(base.Command, base_classes.BaseServiceManagementCommand):
  """Adds or update a quota override setting for a service and a project."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    views = services_util.GetCallerViews()

    consumers_flags.CONSUMER_PROJECT_FLAG.AddToParser(parser)
    consumers_flags.SERVICE_FLAG.AddToParser(parser)

    parser.add_argument(
        '--quota-limit',
        required=True,
        metavar='LIMIT',
        type=arg_parsers.BoundedInt(-1, sys.maxint),
        help='Set the quota configuration limit, 0 to block, -1 for unlimited.')

    override = parser.add_mutually_exclusive_group(required=True)
    override.add_argument(
        '--consumer',
        action='store_true',
        default=False,
        help='Add or update a consumer quota override. Or use --producer')
    override.add_argument(
        '--producer',
        action='store_true',
        default=False,
        help='Add or update a producer quota override. Or use --consumer')

    parser.add_argument(
        '--view',
        default='CONSUMER',
        type=lambda x: str(x).upper(),
        choices=sorted(views.keys()),
        help=('The consumer settings view to use. Choose from {0}').format(
            ', '.join(sorted(views.keys()))))

    # TODO(user): Improve the documentation of these flags with extended help
    parser.add_argument(
        'quota_limit_key',
        help='The quota limit key in this format GroupName/LimitName.')

    base.ASYNC_FLAG.AddToParser(parser)

  @http_error_handler.HandleHttpErrors
  def Run(self, args):
    """Run 'service-management add-quota-override'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the consumer settings API call.
    """
    # Shorten the name for better readability
    patch_request = (self.services_messages
                     .ServicemanagementServicesProjectSettingsPatchRequest)

    quota_override = self.services_messages.QuotaLimitOverride(
        limit=args.quota_limit)

    # Create a QuotaSettings object to store the added override
    if args.consumer:
      overrides = self.services_messages.QuotaSettings.ConsumerOverridesValue()

      overrides.additionalProperties.append(
          self.services_messages.QuotaSettings.ConsumerOverridesValue
          .AdditionalProperty(
              key=args.quota_limit_key,
              value=quota_override)
      )

      quota_settings = self.services_messages.QuotaSettings(
          consumerOverrides=overrides
      )
    elif args.producer:
      overrides = self.services_messages.QuotaSettings.ProducerOverridesValue()

      overrides.additionalProperties.append(
          self.services_messages.QuotaSettings.ProducerOverridesValue
          .AdditionalProperty(
              key=args.quota_limit_key,
              value=quota_override)
      )

      quota_settings = self.services_messages.QuotaSettings(
          producerOverrides=overrides
      )

    project_settings = self.services_messages.ProjectSettings(
        quotaSettings=quota_settings,
    )

    update_mask = 'quota_settings.{0}_overrides["{1}"]'.format(
        'consumer' if args.consumer else 'producer', args.quota_limit_key)
    request = patch_request(
        serviceName=args.service,
        consumerProjectId=args.consumer_project,
        projectSettings=project_settings,
        updateMask=update_mask)

    operation = self.services_client.services_projectSettings.Patch(request)

    return services_util.ProcessOperationResult(operation, args.async)
