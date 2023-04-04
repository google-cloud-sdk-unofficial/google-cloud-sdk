# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Print an Artifact Registry IAM policy for Container Registry to Artifact Registry upgrade."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import flags
from googlecloudsdk.command_lib.artifacts import upgrade_util
from googlecloudsdk.command_lib.artifacts import util


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class PrintIamPolicy(base.Command):
  """Print an Artifact Registry IAM policy for Container Registry to Artifact Registry upgrade.

  Print an Artifact Registry IAM policy that is equivalent to the IAM policy
  applied to the storage bucket for the specified Container Registry hostname.
  Apply the returned policy to the Artifact Registry repository that will
  replace the specified host. By default, this command only considers IAM
  policies within the
  project-level scope, so policies that are at the folder or organization level
  will not be included in the generated policy. To change the scope, use the
  --organization or --folder flags.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
  To print an equivalant Artifact Registry IAM policy for 'gcr.io/my-project' within scope
  `projects/my-project`:

      $ {command} upgrade print-iam-policy gcr.io --project=my-project

  To print an equivalant Artifact Registry IAM policy for 'gcr.io/my-project' within scope
  `folders/123`:

      $ {command} upgrade print-iam-policy gcr.io --project=my-project
      --folder=123

  To print an equivalant Artifact Registry IAM policy for 'gcr.io/my-project' within scope
  `organizations/123`:

      $ {command} upgrade print-iam-policy gcr.io --project=my-project
      --organization=123
  """,
  }

  @staticmethod
  def Args(parser):
    flags.GetGCRDomainArg().AddToParser(parser)
    scope_group = parser.add_mutually_exclusive_group()
    scope_group.add_argument(
        '--organization',
        metavar='ORGANIZATION_ID',
        help=(
            'Organization ID on which to scope IAM analysis. Only policies'
            ' defined at or below this organization will be included in the'
            ' analysis.'
        ),
    )
    scope_group.add_argument(
        '--folder',
        metavar='FOLDER_ID',
        help=(
            'Folder ID on which to scope IAM analysis. Only policies defined at'
            ' or below this folder will be included in the analysis.'
        ),
    )

  def Run(self, args):
    """Runs the command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      An iam.Policy.
    """
    domain = args.DOMAIN
    project = util.GetProject(args)
    parent = 'projects/{0}'.format(project)
    if args.IsSpecified('folder'):
      parent = 'folders/{0}'.format(args.folder)
    if args.IsSpecified('organization'):
      parent = 'organizations/{0}'.format(args.organization)
    return upgrade_util.iam_policy(domain, project, parent)
