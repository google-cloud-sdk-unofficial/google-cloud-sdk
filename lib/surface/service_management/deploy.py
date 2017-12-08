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

from apitools.base.py import encoding

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.service_management import enable_api
from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.api_lib.util import http_error_handler
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

  @http_error_handler.HandleHttpErrors
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

    # Check if the provided file is a swagger spec that needs to be converted
    # to Google Service Configuration
    if 'swagger' in service_config_dict:
      swagger_file = self.services_messages.File(
          contents=config_contents,
          path=os.path.basename(args.service_config_file)
      )
      # TODO(user): Add support for swagger file references later
      # This requires the API to support multiple files first. b/23353397
      swagger_spec = self.services_messages.SwaggerSpec(
          swaggerFiles=[swagger_file])
      request = self.services_messages.ConvertConfigRequest(
          swaggerSpec=swagger_spec,
      )

      response = self.services_client.v1.ConvertConfig(request)
      diagnostics = response.diagnostics
      if diagnostics:
        kind = self.services_messages.Diagnostic.KindValueValuesEnum
        for diagnostic in diagnostics:
          logger = log.error if diagnostic.kind == kind.ERROR else log.warning
          logger('{l}: {m}'.format(l=diagnostic.location, m=diagnostic.message))

        # After all errors and warnings have been printed, exit early if any
        # errors were returned by the server.
        for diagnostic in diagnostics:
          if diagnostic.kind == kind.ERROR:
            raise SwaggerUploadException(
                'Failed to upload service configuration.')

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

    operation = self.services_client.services.Update(request)

    service_name = None
    config_id = None
    # Fish the serviceName and serviceConfig.id fields from the proto Any
    # that is returned in result.response
    for prop in operation.response.additionalProperties:
      if prop.key == 'serviceName':
        service_name = prop.value.string_value
      elif prop.key == 'serviceConfig':
        for item in prop.value.object_value.properties:
          if item.key == 'id':
            config_id = item.value.string_value
            break
      elif prop.key == 'producerProjectId':
        producer_project_id = prop.value.string_value

    if service_name and config_id:
      # Print this to screen not to the log because the output is needed by the
      # human user.
      log.status.Print(
          ('\nService Configuration with version "{0}" uploaded '
           'for service "{1}"\n').format(config_id, service_name))
    else:
      raise calliope_exceptions.ToolException(
          'Failed to retrieve Service Name and Service Configuration Version')

    services_util.ProcessOperationResult(operation, args.async)

    # Check to see if the service is already enabled
    enable_api.EnableServiceIfDisabled(
        producer_project_id, service_name, args.async)
