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

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.third_party.apitools.base.py import encoding
from googlecloudsdk.third_party.apitools.base.py import exceptions as apitools_exceptions


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

  def Run(self, args):
    """Run 'service-management deploy'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the Update API call.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    with open(args.service_config_file, 'r') as f:
      config_contents = f.read()

    # Try to load the file as JSON. If that fails, try YAML.
    service_config_dict = services_util.LoadJsonOrYaml(config_contents)
    if not service_config_dict:
      raise exceptions.BadFileException(
          'Could not read JSON or YAML from service config file %s.'
          % args.service_config_file)

    # Check if the provided file is a swagger spec that needs to be converted
    # to Google Service Configuration
    if 'swagger' in service_config_dict:
      swagger_file = self.services_messages.File(
          contents=config_contents,
          path=args.service_config_file
      )
      # TODO(user): Add support for swagger file references later
      # This requires the API to support multiple files first. b/23353397
      swagger_spec = self.services_messages.SwaggerSpec(
          swaggerFiles=[swagger_file])
      request = self.services_messages.ConvertConfigRequest(
          swaggerSpec=swagger_spec,
      )

      try:
        response = self.services_client.v1.ConvertConfig(request)
      except apitools_exceptions.HttpError as error:
        raise exceptions.HttpException(services_util.GetError(error))

      diagnostics = response.diagnostics
      if diagnostics:
        kind = self.services_messages.Diagnostic.KindValueValuesEnum
        for diagnostic in diagnostics:
          logger = log.error if diagnostic.kind == kind.ERROR else log.warning
          logger('{l}: {m}'.format(l=diagnostic.location, m=diagnostic.message))

      service_config = response.serviceConfig
    else:
      # If not Swagger, assume that we are dealing with Google Service Config
      service_config = encoding.JsonToMessage(
          self.services_messages.Service, config_contents)

    managed_service = self.services_messages.ManagedService(
        serviceConfig=service_config,
        serviceName=service_config.name)

    # Set the serviceConfig producerProjectId if it is not already set
    if not managed_service.serviceConfig.producerProjectId:
      managed_service.serviceConfig.producerProjectId = self.project

    request = self.services_messages.ServicemanagementServicesUpdateRequest(
        serviceName=managed_service.serviceName,
        managedService=managed_service,
    )

    try:
      result = self.services_client.services.Update(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(services_util.GetError(error))

    # Remove the response portion of the resulting operation since
    # it can be extremely large.
    result.response = None

    return services_util.ProcessOperationResult(result)
