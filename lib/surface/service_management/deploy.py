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
        nargs='+',
        help=('The service configuration file (or files) containing the API '
              'specification to upload. Proto Descriptors, Open API (Swagger) '
              'specifications, and Google Service Configuration files in JSON '
              'and YAML formats are acceptable.'))

    base.ASYNC_FLAG.AddToParser(parser)

  def FilenameMatchesExtension(self, filename, extensions):
    f = filename.lower()
    for ext in extensions:
      if f.endswith(ext.lower()):
        return True
    return False

  def MakeConfigFile(self, file_contents, filename, file_type):
    return self.messages.ConfigFile(
        fileContents=file_contents,
        filePath=os.path.basename(filename),
        fileType=file_type,
    )

  def Run(self, args):
    """Run 'service-management deploy'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the Update API call.

    Raises:
      SwaggerUploadException: if the provided service configuration files are
          rejected by the Service Management API.

      BadFileExceptionn: if the provided service configuration files are
          invalid or cannot be read.
    """
    self.messages = services_util.GetMessagesModule()
    file_types = self.messages.ConfigFile.FileTypeValueValuesEnum
    self.service_name = self.service_version = config_contents = None
    config_files = []

    for service_config_file in args.service_config_file:
      config_contents = None
      with open(service_config_file, 'r') as f:
        config_contents = f.read()

      if self.FilenameMatchesExtension(
          service_config_file, ['.json', '.yaml', '.yml']):
        # Try to load the file as JSON. If that fails, try YAML.
        service_config_dict = services_util.LoadJsonOrYaml(config_contents)
        if not service_config_dict:
          raise calliope_exceptions.BadFileException(
              'Could not read JSON or YAML from service config file %s.'
              % args.service_config_file)

        if 'swagger' in service_config_dict:
          if not self.service_name:
            self.service_name = service_config_dict.get('host', None)

          # Always use YAML for Open API because JSON is a subset of YAML.
          config_files.append(
              self.MakeConfigFile(config_contents, service_config_file,
                                  file_types.OPEN_API_YAML))
        elif service_config_dict.get('type') == 'google.api.Service':
          self.service_name = service_config_dict.get('name')

          config_files.append(
              self.MakeConfigFile(config_contents, service_config_file,
                                  file_types.SERVICE_CONFIG_YAML))
        elif 'name' in service_config_dict:
          # This is a special case. If we have been provided a Google Service
          # Configuration file which has a service 'name' field, but no 'type'
          # field, we have to assume that this is a normalized service config,
          # and can be uploaded via the CreateServiceConfig API. Therefore,
          # we can short circute the process here.
          if len(args.service_config_file) > 1:
            raise calliope_exceptions.BadFileException((
                'Ambiguous input. Found normalized service configuration in '
                'file {0}, but received multiple input files. To upload '
                'normalized service config, please provide it separately from '
                'other input files to avoid ambiguity.').format(
                    service_config_file))

          self.service_name = service_config_dict.get('name', None)
          config_files = []
          break
        else:
          raise calliope_exceptions.BadFileException((
              'Unable to parse Open API, or Google Service Configuration '
              'specification from {0}').format(service_config_file))

      elif self.FilenameMatchesExtension(
          service_config_file, ['.pb', '.descriptor']):
        config_files.append(
            self.MakeConfigFile(config_contents, service_config_file,
                                file_types.FILE_DESCRIPTOR_SET_PROTO))
      else:
        raise calliope_exceptions.BadFileException((
            'Could not determine the content type of file {0}. Supported '
            'extensions are .json .yaml .yml .pb. and .descriptor').format(
                service_config_file))

    # Check to see if the Endpoints meta service needs to be enabled.
    enable_api.EnableServiceIfDisabled(
        self.project, services_util.GetEndpointsServiceName(), args.async)
    # Check if we need to create the service.
    services_util.CreateServiceIfNew(self.service_name, self.project)

    if config_files:
      self.service_config_id = services_util.PushMultipleServiceConfigFiles(
          self.service_name, config_files, args.async)
    else:
      self.service_config_id = services_util.PushNormalizedGoogleServiceConfig(
          self.service_name, self.project, config_contents)

    if not self.service_config_id:
      raise calliope_exceptions.ToolException(
          'Failed to retrieve Service Configuration Id.')

    # Create a Rollout for the new service configuration
    percentages = (self.services_messages.TrafficPercentStrategy.
                   PercentagesValue())
    percentages.additionalProperties.append(
        (self.services_messages.TrafficPercentStrategy.PercentagesValue.
         AdditionalProperty(
             key=self.service_config_id,
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
        ('\nService Configuration [{0}] uploaded for '
         'service [{1}]\n').format(self.service_config_id, self.service_name))
