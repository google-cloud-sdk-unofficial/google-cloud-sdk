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

"""service-management set-quota-override command."""

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.service_management import consumers_flags
from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions


class SetQuotaOverride(base.Command, base_classes.BaseServiceManagementCommand):
  """Adds or update a quota override setting for a service and a project."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    consumers_flags.CONSUMER_PROJECT_FLAG.AddToParser(parser)
    consumers_flags.SERVICE_FLAG.AddToParser(parser)

    parser.add_argument(
        '--limit',
        required=True,
        help='The limit to see for this quota. Enter 0 to block access, '
             'or \'unlimited\' for unlimited access.')

    # TODO(user): Improve the documentation of these flags with extended help
    parser.add_argument(
        '--limit-key',
        required=True,
        help='The quota limit key in the format GroupName/LimitName.')

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
    # Sanity check for limit parameter
    if args.limit == 'unlimited':
      args.limit = -1
    elif args.limit.isdigit():
      args.limit = int(args.limit)
    else:
      raise calliope_exceptions.InvalidArgumentException(
          'limit', 'must be an integer >= 0 or \'unlimited\'.')

    # Shorten the name for better readability
    patch_request = (self.services_messages
                     .ServicemanagementServicesProjectSettingsPatchRequest)

    quota_override = self.services_messages.QuotaLimitOverride(
        limit=args.limit)

    # Create a QuotaSettings object to store the added override
    # When the optional consumer-project flag is set, we assume that the
    # command is called by a service producer to act on one of their consumers'
    # projects.
    if args.consumer_project:
      overrides = self.services_messages.QuotaSettings.ProducerOverridesValue()

      overrides.additionalProperties.append(
          self.services_messages.QuotaSettings.ProducerOverridesValue
          .AdditionalProperty(
              key=args.limit_key,
              value=quota_override)
      )

      quota_settings = self.services_messages.QuotaSettings(
          producerOverrides=overrides
      )

      update_mask = 'quota_settings.producer_overrides["{0}"]'.format(
          args.limit_key)
    else:
      overrides = self.services_messages.QuotaSettings.ConsumerOverridesValue()

      overrides.additionalProperties.append(
          self.services_messages.QuotaSettings.ConsumerOverridesValue
          .AdditionalProperty(
              key=args.limit_key,
              value=quota_override)
      )

      quota_settings = self.services_messages.QuotaSettings(
          consumerOverrides=overrides
      )

      update_mask = 'quota_settings.consumer_overrides["{0}"]'.format(
          args.limit_key)

    project_settings = self.services_messages.ProjectSettings(
        quotaSettings=quota_settings,
    )

    consumer_project_id = services_util.GetValidatedProject(
        args.consumer_project)

    request = patch_request(
        serviceName=args.service,
        consumerProjectId=consumer_project_id,
        projectSettings=project_settings,
        updateMask=update_mask)

    operation = self.services_client.services_projectSettings.Patch(request)

    return services_util.ProcessOperationResult(operation, args.async)
