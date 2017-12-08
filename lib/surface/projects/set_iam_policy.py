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

"""Command to set IAM policy for a resource."""

from googlecloudsdk.api_lib.projects import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core.iam import iam_util


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class SetIamPolicy(base.Command):
  """Set IAM policy for a project.

  Sets the IAM policy for a project, given a project ID and a file that
  contains the JSON-encoded IAM policy.
  """

  detailed_help = {
      'brief': 'Set IAM policy for a project.',
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          The following command reads an IAM policy defined in a JSON file
          `policy.json` and sets it for a project with the ID
          `example-project-id-1`:

            $ {command} example-project-id-1 policy.json
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('id', metavar='PROJECT_ID',
                        completion_resource='cloudresourcemanager.projects',
                        list_command_path='projects',
                        help='ID for the project you want to set '
                             'IAM policy.')
    parser.add_argument('policy_file', help='JSON file with the IAM policy')

  @util.HandleHttpError
  def Run(self, args):
    projects = self.context['projects_client']
    messages = self.context['projects_messages']
    resources = self.context['projects_resources']

    project_ref = resources.Parse(args.id,
                                  collection='cloudresourcemanager.projects')

    policy = iam_util.ParseJsonPolicyFile(args.policy_file, messages.Policy)

    policy_request = messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
        resource=project_ref.Name(),
        setIamPolicyRequest=messages.SetIamPolicyRequest(policy=policy))
    return projects.projects.SetIamPolicy(policy_request)

  def Display(self, args, result):
    """This method is called to print the result of the Run() method.

    Args:
      args: The arguments that command was run with.
      result: The value returned from the Run() method.
    """
    # pylint:disable=not-callable, self.format is callable.
    self.format(result)
