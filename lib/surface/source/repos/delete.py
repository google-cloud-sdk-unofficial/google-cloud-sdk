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

"""Delete Google Cloud Platform git repository.
"""

import textwrap

from apitools.base.py import exceptions

from googlecloudsdk.api_lib.source import git
from googlecloudsdk.api_lib.source import source
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.Command):
  """Delete project git repository in the current directory."""

  detailed_help = {
      'DESCRIPTION': """\
          This command deletes a named git repository from the currently
          active Google Cloud Platform project.
      """,
      'EXAMPLES': textwrap.dedent("""\
          To delete a named repository in the current project issue the
          following commands:

            $ gcloud init
            $ gcloud alpha source repos delete REPO_NAME
      """),
  }

  @staticmethod
  def Args(parser):
    # TODO(user): consider adding autocomplete logic for the repository name.
    parser.add_argument(
        'name',
        metavar='REPOSITORY_NAME',
        help=('Name of the repository.'))

  @c_exc.RaiseToolExceptionInsteadOf(git.Error)
  @http_error_handler.HandleHttpErrors
  def Run(self, args):
    """Delete a named GCP repository in the current project.

    Args:
      args: argparse.Namespace, the arguments this command is run with.

    Returns:
      The path to the deleted git repository.

    Raises:
      ToolException: on project initialization errors.
    """

    project_id = properties.VALUES.core.project.Get(required=True)
    project = source.Project(project_id)
    try:
      project.DeleteRepo(args.name)
      log.DeletedResource(args.name)
      return args.name
    except exceptions.HttpError as e:
      message = ('Failed to delete repository [{name}] for Project '
                 '[{prj}] with error [{err}].\n'.format(
                     prj=project_id, name=args.name, err=e))
      raise source.RepoDeletionError(message)
