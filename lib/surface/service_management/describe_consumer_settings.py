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

"""service-management describe-consumer-settings command."""

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.service_management import consumers_flags
from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base


class DescribeConsumerSettings(base.Command,
                               base_classes.BaseServiceManagementCommand):
  """Describes the consumer settings for a service and a project."""

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

  @http_error_handler.HandleHttpErrors
  def Run(self, args):
    """Run 'service-management describe-consumer-settings'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the consumer settings API call.
    """
    # Shorten the request name for better readability
    get_request = (self.services_messages
                   .ServicemanagementServicesProjectSettingsGetRequest)

    # When the optional consumer-project flag is set, we assume that the
    # command is called by a service producer to act on one of their consumers'
    # projects.
    views = services_util.GetCallerViews()
    view = views['PRODUCER'] if args.consumer_project else views['CONSUMER']

    consumer_project_id = services_util.GetValidatedProject(
        args.consumer_project)

    request = get_request(
        serviceName=args.service,
        consumerProjectId=consumer_project_id,
        view=view
    )

    return self.services_client.services_projectSettings.Get(request)
