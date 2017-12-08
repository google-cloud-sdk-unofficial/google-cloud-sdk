# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Create a Google Cloud Platform git repository.
"""

import textwrap
from apitools.base.py import exceptions

from googlecloudsdk.api_lib.source import git
from googlecloudsdk.api_lib.source import source
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.command_lib.source import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a named git repo for the project in the current directory."""

  detailed_help = {
      'DESCRIPTION': """\
          This command creates a named git repository for the currently
          active Google Cloud Platform project.
      """,
      'EXAMPLES': textwrap.dedent("""\
          To create a named repository in the current project issue the
          following commands:

            $ gcloud init
            $ gcloud alpha source repos create REPO_NAME

          Once you push contents to it, they can be browsed in the
          Developers Console.
      """),
  }

  @staticmethod
  def Args(parser):
    name = parser.add_argument(
        'name',
        metavar='REPOSITORY_NAME',
        type=flags.REPO_NAME_VALIDATOR,
        help=('Name of the repository.'))
    name.detailed_help = """\
        Name of the repository. May contain between 3 and 63 (inclusive)
        lowercase letters, digits, and hyphens. Must start with a letter, and
        may not end with a hyphen.
        """

  @c_exc.RaiseToolExceptionInsteadOf(git.Error)
  def Run(self, args):
    """Create a GCP repository to the current directory.

    Args:
      args: argparse.Namespace, the arguments this command is run with.

    Returns:
      The path to the new git repository.

    Raises:
      ToolException: on project initialization errors.
      RepoCreationError: on repo creation errors.
    """

    project_id = properties.VALUES.core.project.Get(required=True)
    project = source.Project(project_id)
    try:
      path = project.CreateRepo(args.name)
      log.CreatedResource(path)
      return path
    except exceptions.HttpError as e:
      message = ('Failed to create repository [{name}] for Project '
                 '[{prj}] with error [{err}].\n'.format(
                     prj=project_id, name=args.name, err=e))
      raise source.RepoCreationError(message)
