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

import textwrap
from googlecloudsdk.api_lib.projects import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import list_printer
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Update(base.Command):
  """Update the name of a Project."""

  detailed_help = {
      'brief': 'Update a project.',
      'DESCRIPTION': textwrap.dedent("""\
          Updates the given project with new name.

          This command can fail for the following reasons:
              * There is no project with the given ID.
              * The active account does not have Owner or Editor permissions for
                the given project.
    """),
      'EXAMPLES': textwrap.dedent("""\
          The following command updates a project with the ID
          `example-foo-bar-1` to have the name "Foo Bar and Grill":

            $ {command} example-foo-bar-1 --name="Foo Bar and Grill"
    """),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('id', metavar='PROJECT_ID',
                        completion_resource='cloudresourcemanager.projects',
                        list_command_path='projects',
                        help='ID for the project you want to update.')
    parser.add_argument('--name', required=True,
                        help='New name for the project.')

  @util.HandleHttpError
  def Run(self, args):
    projects = self.context['projects_client']
    messages = self.context['projects_messages']
    resources = self.context['projects_resources']
    project_ref = resources.Parse(args.id,
                                  collection='cloudresourcemanager.projects')
    result = projects.projects.Update(
        messages.Project(
            projectId=project_ref.Name(),
            name=args.name))
    log.UpdatedResource(project_ref)
    return result

  def Display(self, args, result):
    """This method is called to print the result of the Run() method.

    Args:
      args: The arguments that command was run with.
      result: The value returned from the Run() method.
    """
    list_printer.PrintResourceList('cloudresourcemanager.projects', [result])
