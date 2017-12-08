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

"""Command to get IAM policy for a resource."""

from googlecloudsdk.api_lib.projects import util
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class GetIamPolicy(base.Command):
  """Get IAM policy for a Project.

  Gets the IAM policy for a project, given a project ID.
  """

  detailed_help = {
      'brief': 'Get IAM policy for a project.',
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          The following command prints the IAM policy for a project with
          the ID `example-project-id-1`:

            $ {command} example-project-id-1
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('id', metavar='PROJECT_ID',
                        completion_resource='cloudresourcemanager.projects',
                        list_command_path='projects',
                        help='ID for the project whose policy you want to get.')

  @util.HandleHttpError
  def Run(self, args):
    projects = self.context['projects_client']
    messages = self.context['projects_messages']
    resources = self.context['projects_resources']

    project_ref = resources.Parse(args.id,
                                  collection='cloudresourcemanager.projects')
    policy_request = messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
        resource=project_ref.Name(),
        getIamPolicyRequest=messages.GetIamPolicyRequest(),
    )
    return projects.projects.GetIamPolicy(policy_request)

  def Display(self, args, result):
    """This method is called to print the result of the Run() method.

    Args:
      args: The arguments that command was run with.
      result: The value returned from the Run() method.
    """
    # pylint:disable=not-callable, self.format is callable.
    self.format(result)
