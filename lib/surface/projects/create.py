# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Command to create a new project."""

from googlecloudsdk.api_lib.projects import util
from googlecloudsdk.api_lib.service_management import enable_api
from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import util as command_lib_util
from googlecloudsdk.core import apis
from googlecloudsdk.core import log


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a new project.

  Creates a new project with the given project ID.
  """

  detailed_help = {
      'EXAMPLES': """
          The following command creates a project with the ID
          `example-foo-bar-1` and the name `Happy project`:

            $ {command} example-foo-bar-1 --name="Happy project"
      """,
  }

  def Collection(self):
    return command_lib_util.PROJECTS_COLLECTION

  def GetUriFunc(self):
    return command_lib_util.ProjectsUriFunc

  @staticmethod
  def Args(parser):
    parser.add_argument('id', metavar='PROJECT_ID',
                        help='ID for the project you want to create.')
    parser.add_argument('--name',
                        help='Name for the project you want to create. '
                             'If not specified, will use project id as name.')
    parser.add_argument('--enable-cloud-apis',
                        action='store_true',
                        default=True,
                        help='Enable cloudapis.googleapis.com during creation.')

  # util.HandleKnownHttpErrors needs to be the first one to handle errors.
  # It needs to be placed after http_error_handler.HandleHttpErrors.
  @http_error_handler.HandleHttpErrors
  @util.HandleKnownHttpErrors
  def Run(self, args):
    projects = util.GetClient()
    messages = util.GetMessages()

    project_ref = command_lib_util.ParseProject(args.id)

    # Create project.
    project_creation_result = projects.projects.Create(
        messages.Project(
            projectId=project_ref.Name(),
            name=args.name if args.name else project_ref.Name()))

    if args.enable_cloud_apis:
      # Enable cloudapis.googleapis.com
      services_client = apis.GetClientInstance('servicemanagement', 'v1')
      enable_operation = enable_api.EnableServiceApiCall(
          project_ref.Name(), 'cloudapis.googleapis.com')
      services_util.WaitForOperation(enable_operation.name, services_client)
      # TODO(user): Retry in case it failed?

    log.CreatedResource(project_ref)
    return project_creation_result
