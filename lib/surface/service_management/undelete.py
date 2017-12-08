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
"""service-management undelete command."""

from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.service_management import common_flags


class Undelete(base.Command):
  """Undeletes a service configuration given a service name.

  Note: This command is effective for up to 30 days after a service
  configuration has been marked for deletion.
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    common_flags.producer_service_flag(suffix='to undelete').AddToParser(parser)

    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run 'service-management undelete'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the Undelete API call (or None if cancelled).
    """
    messages = services_util.GetMessagesModule()
    client = services_util.GetClientInstance()
    request = messages.ServicemanagementServicesUndeleteRequest(
        serviceName=args.service,)

    operation = client.services.Undelete(request)

    return services_util.ProcessOperationResult(operation, args.async)
