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

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import util as command_lib_util
from googlecloudsdk.command_lib.util import labels_util

from googlecloudsdk.core import log


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a new project.

  Creates a new project with the given project ID.
  """

  detailed_help = {
      'EXAMPLES': """
          The following command creates a project with ID
          `example-foo-bar-1`, name `Happy project` and label `type=happy`:

            $ {command} example-foo-bar-1 --name="Happy project" --labels=type=happy
      """,
  }

  def Collection(self):
    return command_lib_util.PROJECTS_COLLECTION

  def GetUriFunc(self):
    return command_lib_util.ProjectsUriFunc

  @staticmethod
  def Args(parser):
    labels_util.AddCreateLabelsFlags(parser)
    parser.add_argument('id', metavar='PROJECT_ID',
                        help='ID for the project you want to create.')
    parser.add_argument('--name',
                        help='Name for the project you want to create. '
                             'If not specified, will use project id as name.')
    parser.add_argument('--enable-cloud-apis',
                        action='store_true',
                        default=True,
                        help='Enable cloudapis.googleapis.com during creation.')

  @http_error_handler.HandleHttpErrors
  def Run(self, args):
    project_ref = command_lib_util.ParseProject(args.id)
    result = projects_api.Create(
        project_ref,
        args.name,
        args.enable_cloud_apis,
        update_labels=labels_util.GetUpdateLabelsDictFromArgs(args))
    log.CreatedResource(project_ref)
    return result
