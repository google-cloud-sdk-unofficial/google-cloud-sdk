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

"""service-management remove-quota-override command."""

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.service_management import consumers_flags
from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


class RemoveQuota(base.Command, base_classes.BaseServiceManagementCommand):
  """Removes a quota override setting for a service and a project."""

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

    # TODO(user): Improve the documentation of these flags with extended help
    parser.add_argument(
        '--limit-key',
        help='The quota limit key in the format GroupName/LimitName.')

    base.ASYNC_FLAG.AddToParser(parser)

  @http_error_handler.HandleHttpErrors
  def Run(self, args):
    """Run 'service-management remove-quota-override'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the consumer settings API call.
    """
    # Shorten the request names for better readability
    get_request = (self.services_messages
                   .ServicemanagementServicesProjectSettingsGetRequest)
    patch_request = (self.services_messages
                     .ServicemanagementServicesProjectSettingsPatchRequest)

    # When the optional consumer-project flag is set, we assume that the
    # command is called by a service producer to act on one of their consumers'
    # projects.
    views = services_util.GetCallerViews()
    view = views['PRODUCER'] if args.consumer_project else views['CONSUMER']

    consumer_project_id = services_util.GetValidatedProject(
        args.consumer_project)

    # Get the current list of quota settings to see if the quota override
    # exists in the first place.
    request = get_request(
        serviceName=args.service,
        consumerProjectId=consumer_project_id,
        view=view,
    )

    response = self.services_client.services_projectSettings.Get(request)

    # Check to see if the quota override was present in the first place.
    override_present = False
    overrides = None
    if args.consumer_project:
      if response.quotaSettings and response.quotaSettings.producerOverrides:
        overrides = response.quotaSettings.producerOverrides
      else:
        overrides = (self.services_messages.QuotaSettings
                     .ProducerOverridesValue())
    else:
      if response.quotaSettings and response.quotaSettings.consumerOverrides:
        overrides = response.quotaSettings.consumerOverrides
      else:
        overrides = (self.services_messages.QuotaSettings
                     .ConsumerOverridesValue())

    if overrides:
      for override in overrides.additionalProperties:
        if override.key == args.limit_key:
          override_present = True
          break

    if not override_present:
      log.warn('No quota override found for "{0}"'.format(args.limit_key))
      return

    project_settings = self.services_messages.ProjectSettings(
        quotaSettings=self.services_messages.QuotaSettings(),
    )

    update_mask = 'quota_settings.{0}_overrides["{1}"]'.format(
        'producer' if args.consumer_project else 'consumer', args.limit_key)

    request = patch_request(
        serviceName=args.service,
        consumerProjectId=consumer_project_id,
        projectSettings=project_settings,
        updateMask=update_mask)

    operation = self.services_client.services_projectSettings.Patch(request)

    return services_util.ProcessOperationResult(operation, args.async)
