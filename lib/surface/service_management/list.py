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

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


class List(base.ListCommand, base_classes.BaseServiceManagementCommand):
  """List service-management for the consumer project."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """

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

    # Remove unneeded list-related flags from parser
    base.URI_FLAG.RemoveFromParser(parser)
    base.FLATTEN_FLAG.RemoveFromParser(parser)

  @http_error_handler.HandleHttpErrors
  def Run(self, args):
    """Run 'service-management list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The list of managed services for this project.
    """
    if args.simple_list:
      args.format = 'value(serviceName)'

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

    return list_pager.YieldFromList(
        self.services_client.services,
        request,
        limit=args.limit,
        batch_size_attribute='pageSize',
        batch_size=args.page_size,
        field='services')

  def Collection(self):
    return 'servicemanagement-v1.services'

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
