
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

"""service-management remove-visibility-label command."""

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.service_management import consumers_flags
from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions


class RemoveVisibilityLabel(base.Command,
                            base_classes.BaseServiceManagementCommand):
  """Removes a visibility label for a service for a consumer project."""

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

    parser.add_argument('label', help='The label to remove.')

    base.ASYNC_FLAG.AddToParser(parser)

  @http_error_handler.HandleHttpErrors
  def Run(self, args):
    """Run 'service-management remove-visibility-label'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the consumer settings API call.

    Raises:
      ToolException: The label that was supposed to be removed is not currently
          set for the given service and consumer project.
    """
    # Shorten the request names for better readability
    get_request = (self.services_messages
                   .ServicemanagementServicesProjectSettingsGetRequest)
    patch_request = (self.services_messages
                     .ServicemanagementServicesProjectSettingsPatchRequest)

    # TODO(user): change this to a conditional update once the service
    # supports it. Until then...
    #
    # 1. Get the current labels

    request = get_request(
        serviceName=args.service,
        consumerProjectId=args.consumer_project,
        view=get_request.ViewValueValuesEnum.PRODUCER_VIEW,
    )

    response = self.services_client.services_projectSettings.Get(request)

    # 2. Remove the provided label from the current labels if it exists
    visibility_labels = []
    if (response.visibilitySettings
        and response.visibilitySettings.visibilityLabels):
      visibility_labels.extend(response.visibilitySettings.visibilityLabels)
    if args.label in visibility_labels:
      visibility_labels.remove(args.label)
    else:
      raise exceptions.ToolException(
          ('Label {0} is not currently applied to service {1} for consumer '
           'project {2}').format(
               args.label, args.service, args.consumer_project))

    visibility_settings = self.services_messages.VisibilitySettings(
        visibilityLabels=visibility_labels
    )
    project_settings = self.services_messages.ProjectSettings(
        visibilitySettings=visibility_settings,
    )
    request = patch_request(
        serviceName=args.service,
        consumerProjectId=args.consumer_project,
        projectSettings=project_settings,
        updateMask='visibility_settings.visibility_labels')

    operation = self.services_client.services_projectSettings.Patch(request)

    return services_util.ProcessOperationResult(operation, args.async)
