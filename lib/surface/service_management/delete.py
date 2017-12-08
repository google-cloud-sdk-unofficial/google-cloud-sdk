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

"""service-management delete command."""

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.service_management import common_flags
from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core.console import console_io


class Delete(base.Command, base_classes.BaseServiceManagementCommand):
  """Deletes a service configuration given the service name."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    common_flags.service_flag(suffix='to delete').AddToParser(parser)

    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run 'service-management delete'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the Delete API call (or None if cancelled).
    """
    # Prompt with a warning before continuing.
    continue_prompt_response = console_io.PromptContinue(
        message='Are you sure? This will permanently delete the service '
                'configuration and all of the associated consumer '
                'information. This CANNOT be undone!',
        prompt_string='Continue anyway',
        default=True,
        throw_if_unattended=True)
    if not continue_prompt_response:
      return

    request = self.services_messages.ServicemanagementServicesDeleteRequest(
        serviceName=args.service,
    )

    operation = self.services_client.services.Delete(request)

    return services_util.ProcessOperationResult(operation, args.async)
