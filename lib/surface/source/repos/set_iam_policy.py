# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Sets the IAM policy for the repository.
"""

import textwrap

from googlecloudsdk.api_lib.sourcerepo import sourcerepo
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import resolvers
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetIamPolicy(base.UpdateCommand):
  """Sets the IAM policy for the named repository."""

  detailed_help = {
      'DESCRIPTION':
          """\
          This command sets the IAM policy for the given repository from the
          policy in the provided file.
      """,
      'EXAMPLES':
          textwrap.dedent("""\
          To set the IAM policy, issue the following command:
            $ gcloud alpha source repos set-iam-policy REPO_NAME POLICY_FILE
      """),
  }

  def Format(self, unused_args):
    """Overrides super.Format to set the default printing style to yaml."""
    return 'yaml'

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'name', metavar='REPOSITORY_NAME', help=('Name of the repository.'))
    parser.add_argument(
        'policy_file',
        metavar='FILE_NAME',
        help=('JSON file with IAM policy. '
              'See https://cloud.google.com/resource-manager/'
              'reference/rest/Shared.Types/Policy'))

  def Run(self, args):
    """Sets the IAM policy for the repository.

    Args:
      args: argparse.Namespace, the arguments this command is run with.

    Returns:
      (sourcerepo_v1_messsages.Policy) The IAM policy.

    Raises:
      ToolException: on project initialization errors.
    """
    project_id = resolvers.FromProperty(properties.VALUES.core.project)

    res = resources.REGISTRY.Parse(
        args.name,
        params={'projectsId': project_id},
        collection='sourcerepo.projects.repos')
    policy = iam_util.ParseJsonPolicyFile(args.policy_file,
                                          sourcerepo.messages.Policy)
    source = sourcerepo.Source()
    return source.SetIamPolicy(res, policy)
