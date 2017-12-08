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

"""service-management versions describe command."""

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base


class Describe(base.DescribeCommand, base_classes.BaseServiceManagementCommand):
  """Describes the configuration for a given version of a service."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument('version',
                        nargs='?',
                        default=None,
                        help='The particular version for which to retrieve '
                             'the configuration. Defaults to the active '
                             'version.')

    parser.add_argument(
        '--service',
        required=True,
        help='The service from which to retrieve the configuration.')

  @http_error_handler.HandleHttpErrors
  def Run(self, args):
    """Run 'service-management versions describe'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the Get API call.
    """

    # Check if the user wants the latest version or a specified version.
    if args.version:
      return self._GetSpecificVersionConfig(args.service, args.version)
    else:
      return self._GetLatestVersionConfig(args.service)

  def _GetSpecificVersionConfig(self, service, version):
    request = self.services_messages.ServicemanagementServicesConfigsGetRequest(
        serviceName=service,
        configId=version)
    return self.services_client.services_configs.Get(request)

  def _GetLatestVersionConfig(self, service):
    request = self.services_messages.ServicemanagementServicesGetRequest(
        serviceName=service,
        expand='service_config')
    service_result = self.services_client.services.Get(request)

    # Return the service config from the service result
    return service_result.serviceConfig
