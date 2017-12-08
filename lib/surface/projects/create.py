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

import textwrap
from googlecloudsdk.api_lib.projects import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import list_printer
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Create a new Project."""

  detailed_help = {
      'brief': 'Create a new project.',
      'DESCRIPTION': textwrap.dedent("""\
          Creates a new project with the given project ID.

          This command can fail for the following reasons:
              * The project specified does not exist.
              * The active account does not have permission to access the given
                project.
    """),
      'EXAMPLES': textwrap.dedent("""\
          The following command creates a project with the ID
          `example-foo-bar-1`:

            $ {command} example-foo-bar-1
    """),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('id', metavar='PROJECT_ID',
                        help='ID for the project you want to create.')
    parser.add_argument('--name',
                        help='Name for the project you want to create.')

  @util.HandleHttpError
  def Run(self, args):
    projects = self.context['projects_client']
    messages = self.context['projects_messages']
    resources = self.context['projects_resources']
    # TODO(user): handle invalid names/ project ids nicely
    project_ref = resources.Parse(args.id,
                                  collection='cloudresourcemanager.projects')
    result = projects.projects.Create(
        messages.Project(
            projectId=project_ref.Name(),
            name=args.name))
    log.CreatedResource(project_ref)
    return result

  def Display(self, args, result):
    """This method is called to print the result of the Run() method.

    Args:
      args: The arguments that command was run with.
      result: The value returned from the Run() method.
    """
    list_printer.PrintResourceList('cloudresourcemanager.projects', [result])
