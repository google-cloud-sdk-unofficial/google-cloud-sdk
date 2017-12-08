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

"""Command to update a new project."""

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.cloudresourcemanager import projects_util
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import flags
from googlecloudsdk.command_lib.projects import util as command_lib_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Update(base.Command):
  """Update the name of a project.

  Updates the given project with new name.

  This command can fail for the following reasons:
  * There is no project with the given ID.
  * The active account does not have Owner or Editor permissions for the
    given project.
  """

  detailed_help = {
      'EXAMPLES': """
          The following command updates a project with the ID
          `example-foo-bar-1` to have the name "Foo Bar and Grill":

            $ {command} example-foo-bar-1 --name="Foo Bar and Grill"
      """,
  }

  def Collection(self):
    return command_lib_util.PROJECTS_COLLECTION

  def GetUriFunc(self):
    return command_lib_util.ProjectsUriFunc

  @staticmethod
  def Args(parser):
    flags.GetProjectFlag('update').AddToParser(parser)
    parser.add_argument('--name', required=True,
                        help='New name for the project.')

  def Format(self, args):
    return self.ListFormat(args)

  # HandleKnownHttpErrors needs to be the first one to handle errors.
  # It needs to be placed after http_error_handler.HandleHttpErrors.
  @http_error_handler.HandleHttpErrors
  @projects_util.HandleKnownHttpErrors
  def Run(self, args):
    project_ref = command_lib_util.ParseProject(args.id)
    result = projects_api.Update(project_ref, name=args.name)
    log.UpdatedResource(project_ref)
    return result
