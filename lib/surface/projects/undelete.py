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

"""Command to undelete a project."""

import textwrap
from googlecloudsdk.api_lib.projects import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Undelete(base.Command):
  """Undelete a Project."""

  detailed_help = {
      'brief': 'Undelete a project.',
      'DESCRIPTION': textwrap.dedent("""\
          Undeletes the project with the given Project ID.

          This command can fail for the following reasons:
              * There is no project with the given ID.
              * The active account does not have Owner or Editor permissions for
                the given project.
    """),
      'EXAMPLES': textwrap.dedent("""\
          The following command undeletes the project with the ID
          `example-foo-bar-1`:

            $ {command} example-foo-bar-1
    """),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('id', metavar='PROJECT_ID',
                        help='ID for the project you want to undelete.')

  @util.HandleHttpError
  def Run(self, args):
    projects = self.context['projects_client']
    messages = self.context['projects_messages']
    resources = self.context['projects_resources']
    project_ref = resources.Parse(args.id,
                                  collection='cloudresourcemanager.projects')
    result = projects.projects.Undelete(
        messages.CloudresourcemanagerProjectsUndeleteRequest(
            projectId=project_ref.Name()))
    log.status.write('Undeleted [{r}].\n'.format(r=project_ref))
    return result
