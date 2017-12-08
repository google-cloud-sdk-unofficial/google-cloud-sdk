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

"""Command to delete a project."""

import textwrap
from googlecloudsdk.api_lib.projects import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Delete(base.Command):
  """Delete a Project."""

  detailed_help = {
      'brief': 'Delete a project.',
      'DESCRIPTION': textwrap.dedent("""\
          Deletes the project with the given project ID.

          This command can fail for the following reasons:
              * The project specified does not exist.
              * The active account does not have Owner permissions for
                the given project.
    """),
      'EXAMPLES': textwrap.dedent("""\
          The following command deletes the project with the ID
          `example-foo-bar-1`:

            $ {command} example-foo-bar-1
    """),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('id', metavar='PROJECT_ID',
                        completion_resource='cloudresourcemanager.projects',
                        list_command_path='projects',
                        help='ID for the project you want to delete.')

  @util.HandleHttpError
  def Run(self, args):
    projects = self.context['projects_client']
    messages = self.context['projects_messages']
    resources = self.context['projects_resources']
    project_ref = resources.Parse(args.id,
                                  collection='cloudresourcemanager.projects')
    if not console_io.PromptContinue('Your project will be deleted.'):
      return None
    result = projects.projects.Delete(
        messages.CloudresourcemanagerProjectsDeleteRequest(
            projectId=project_ref.Name()))
    log.DeletedResource(project_ref)
    return result
