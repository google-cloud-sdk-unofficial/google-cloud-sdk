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

"""service-management list command."""

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import list_printer
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.third_party.apitools.base.py import exceptions as apitools_exceptions


class List(base.Command, base_classes.BaseServiceManagementCommand):
  """List service-management for the consumer project."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument('--limit',
                        type=int,
                        help='The maximum number of results to list.')

    parser.add_argument('--simple-list',
                        action='store_true',
                        default=False,
                        help=('If true, only the list of resource IDs is '
                              'printed. If false, a human-readable table of '
                              'resource information is printed.'))

    mode_group = parser.add_mutually_exclusive_group(required=False)

    mode_group.add_argument('--enabled',
                            action='store_true',
                            help=('(DEFAULT) Return the services the project '
                                  'has enabled for consumption. Or use one of '
                                  '--produced or --available.'))

    mode_group.add_argument('--produced',
                            action='store_true',
                            help=('Return the services that the project '
                                  'produces. Or use one of --enabled or '
                                  '--available.'))

    mode_group.add_argument('--available',
                            action='store_true',
                            help=('Return the services available to the '
                                  'project for consumption. This list will '
                                  'include those services the project '
                                  'already consumes. Or use one of --enabled '
                                  'or --produced.'))

    parser.add_argument('--project-id',
                        dest='project',
                        default=None,
                        help=('The project ID to retrieve information about. '
                              'The default is the currently active project.'))

  def Run(self, args):
    """Run 'service-management list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The list of managed services for this project.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    # Default mode is --enabled, so if no flags were specified,
    # turn on the args.enabled flag.
    if not (args.enabled or args.available or args.produced):
      args.enabled = True

    validated_project = self._GetValidatedProject(args.project)

    if args.enabled:
      request = self._GetEnabledListRequest(validated_project)
    elif args.available:
      request = self._GetAvailableListRequest(validated_project)
    elif args.produced:
      request = self._GetProducedListRequest(validated_project)

    # TODO(user): Implement pagination and --limit
    try:
      response = self.services_client.services.List(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(services_util.GetError(error))

    return response.services or []

  def Display(self, args, result):
    """Display prints information about what just happened to stdout.

    Args:
      args: The same as the args in Run.

      result: a list of ManagedService objects.

    Raises:
      ValueError: if result is None or not a list
    """
    if not result:
      log.status.write(
          ('No managed services were found in your project: {0}\n').format(
              self._GetValidatedProject(args.project)))
      return
    if args.simple_list:
      for service in result:
        log.Print(service.serviceName)
    else:
      list_printer.PrintResourceList('servicemanagement-v1.services', result)

  def _GetEnabledListRequest(self, project_id):
    return self.services_messages.ServicemanagementServicesListRequest(
        consumerProjectId=project_id
    )

  # These are special settings that will make Inception return
  # all service-management available to a project.
  _AVAILABLE_SERVICES_CATEGORY = ('servicemanagement.googleapis.com/'
                                  'categories/google-services')
  _AVAILABLE_SERVICES_EXPAND = 'consumerSettings'

  def _GetAvailableListRequest(self, project_id):
    return self.services_messages.ServicemanagementServicesListRequest(
        consumerProjectId=project_id,
        category=self._AVAILABLE_SERVICES_CATEGORY,
        expand=self._AVAILABLE_SERVICES_EXPAND,
    )

  def _GetProducedListRequest(self, project_id):
    return self.services_messages.ServicemanagementServicesListRequest(
        producerProjectId=project_id
    )

  def _GetValidatedProject(self, project_id):
    # If supplied a project explicitly, validate it, then return it.
    if project_id:
      properties.VALUES.core.project.Validate(project_id)
    else:
      project_id = properties.VALUES.core.project.Get(required=True)
    return project_id
