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

"""service-management deploy command."""

import os

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.service_management import enable_api
from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


class SwaggerUploadException(exceptions.Error):

  def __init(self, message):
    super(SwaggerUploadException, self).__init__(message)


class Deploy(base.Command, base_classes.BaseServiceManagementCommand):
  """Deploys a service configuration for the given service name."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        'service_config_file',
        help=('The service configuration file containing the API '
              'specification to upload. Either a Swagger or Google Service '
              'Config JSON file is expected.'))

    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run 'service-management deploy'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the Update API call.

    Raises:
      SwaggerUploadException: if the provided service configuration file is
          rejected by the Service Management API.

      BadFileExceptionn: if the provided service configuration file is invalid
          or cannot be read.
    """
    with open(args.service_config_file, 'r') as f:
      config_contents = f.read()

    # Try to load the file as JSON. If that fails, try YAML.
    service_config_dict = services_util.LoadJsonOrYaml(config_contents)
    if not service_config_dict:
      raise calliope_exceptions.BadFileException(
          'Could not read JSON or YAML from service config file %s.'
          % args.service_config_file)

    # Check to see if the Endpoints meta service needs to be enabled.
    enable_api.EnableServiceIfDisabled(
        self.project, services_util.GetEndpointsServiceName(), args.async)

    # Get the service name out of the service configuration
    if 'swagger' in service_config_dict:
      self.service_name = service_config_dict.get('host', None)
      # Check if we need to create the service.
      services_util.CreateServiceIfNew(self.service_name, self.project)
      # Push the service configuration.
      self.service_version = services_util.PushOpenApiServiceConfig(
          self.service_name, config_contents,
          os.path.basename(args.service_config_file), args.async)
    else:
      self.service_name = service_config_dict.get('name', None)
      # Check if we need to create the service.
      services_util.CreateServiceIfNew(self.service_name, self.project)
      # Push the service configuration.
      self.service_version = services_util.PushGoogleServiceConfig(
          self.service_name, self.project, config_contents)

    if not self.service_version:
      raise calliope_exceptions.ToolException(
          'Failed to retrieve Service Configuration Version')

    # Create a Rollout for the new service configuration
    percentages = (self.services_messages.TrafficPercentStrategy.
                   PercentagesValue())
    percentages.additionalProperties.append(
        (self.services_messages.TrafficPercentStrategy.PercentagesValue.
         AdditionalProperty(
             key=self.service_version,
             value=100.0)))
    traffic_percent_strategy = (
        self.services_messages.TrafficPercentStrategy(percentages=percentages))
    rollout = self.services_messages.Rollout(
        serviceName=self.service_name,
        trafficPercentStrategy=traffic_percent_strategy,
    )
    rollout_operation = self.services_client.services_rollouts.Create(rollout)
    services_util.ProcessOperationResult(rollout_operation, args.async)

    # Check to see if the service is already enabled
    enable_api.EnableServiceIfDisabled(
        self.project, self.service_name, args.async)

  def Epilog(self, resources_were_displayed):
    # Print this to screen not to the log because the output is needed by the
    # human user.
    log.status.Print(
        ('\nService Configuration with version [{0}] uploaded for '
         'service [{1}]\n').format(self.service_version, self.service_name))
