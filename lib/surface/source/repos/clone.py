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

"""Clone Google Cloud Platform git repository.
"""

import textwrap
from apitools.base.py import exceptions

from googlecloudsdk.api_lib.source import git
from googlecloudsdk.api_lib.source import source
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import store as c_store


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class CloneGA(base.Command):
  """Clone project git repository in the current directory."""

  detailed_help = {
      'DESCRIPTION': """\
          This command clones git repository for the currently active
          Google Cloud Platform project into the specified folder in the
          current directory.
      """,
      'EXAMPLES': textwrap.dedent("""\
          To use the default Google Cloud repository for development, use the
          following commands. We recommend that you use your project name as
          TARGET_DIR to make it apparent which directory is used for which
          project. We also recommend to clone the repository named 'default'
          since it is automatically created for each project, and its
          contents can be browsed and edited in the Developers Console.

            $ gcloud init
            $ gcloud source repos clone default TARGET_DIR
            $ cd TARGET_DIR
            ... create/edit files and create one or more commits ...
            $ git push origin master
      """),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help=('If provided, prints the command that would be run to standard '
              'out instead of executing it.'))

    parser.add_argument(
        'src',
        metavar='REPOSITORY_NAME',
        help=('Name of the repository. '
              'Note: Google Cloud Platform projects generally have (if '
              'created) a repository named "default"'))
    parser.add_argument(
        'dst',
        metavar='DIRECTORY_NAME',
        nargs='?',
        help=('Directory name for the cloned repo. Defaults to the repository '
              'name.'))

  @c_exc.RaiseToolExceptionInsteadOf(git.Error, c_store.Error)
  def Run(self, args):
    """Clone a GCP repository to the current directory.

    Args:
      args: argparse.Namespace, the arguments this command is run with.

    Raises:
      ToolException: on project initialization errors.

    Returns:
      The path to the new git repository.
    """
    # Ensure that we're logged in.
    c_store.Load()

    project_id = properties.VALUES.core.project.Get(required=True)
    project_repo = git.Git(project_id, args.src)
    path = project_repo.Clone(destination_path=args.dst or args.src,
                              dry_run=args.dry_run)
    if path and not args.dry_run:
      log.status.write('Project [{prj}] repository [{repo}] was cloned to '
                       '[{path}].\n'.format(prj=project_id, path=path,
                                            repo=project_repo.GetName()))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CloneAlpha(base.Command):
  """Clone project git repository in the current directory."""

  detailed_help = {
      'DESCRIPTION': """\
          This command clones git repository for the currently active
          Google Cloud Platform project into the specified folder in the
          current directory.
      """,
      'EXAMPLES': textwrap.dedent("""\
          To use the default Google Cloud repository for development, use the
          following commands. We recommend that you use your project name as
          TARGET_DIR to make it apparent which directory is used for which
          project. We also recommend to clone the repository named 'default'
          since it is automatically created for each project, and its
          contents can be browsed and edited in the Developers Console.

            $ gcloud init
            $ gcloud source repos clone default TARGET_DIR
            $ cd TARGET_DIR
            ... create/edit files and create one or more commits ...
            $ git push origin master
      """),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help=('If provided, prints the command that would be run to standard '
              'out instead of executing it.'))
    parser.add_argument(
        '--autocreate',
        action='store_true',
        help=('If true, creates a named repo without prompting the user if the '
              'repo does not already exist.'))

    parser.add_argument(
        'src',
        metavar='REPOSITORY_NAME',
        help=('Name of the repository. '
              'Note: Google Cloud Platform projects generally have (if '
              'created) a repository named "default"'))
    parser.add_argument(
        'dst',
        metavar='DIRECTORY_NAME',
        nargs='?',
        help=('Directory name for the cloned repo. Defaults to the repository '
              'name.'))

  @c_exc.RaiseToolExceptionInsteadOf(git.Error, c_store.Error)
  def Run(self, args):
    """Clone a GCP repository to the current directory.

    Args:
      args: argparse.Namespace, the arguments this command is run with.

    Raises:
      ToolException: on project initialization errors.
      RepoCreationError: on repo creation errors.

    Returns:
      The path to the new git repository.
    """
    # Ensure that we're logged in.
    c_store.Load()

    project_id = properties.VALUES.core.project.Get(required=True)
    # Check for the existence of the named repo in the project and maybe ask
    # the user whether they want to create it if it does not already exist.
    #
    # Note that repo creation can fail if there is a concurrent attempt to
    # create the repo (e.g. through another call to gcloud or a concurrent
    # attempt in the developer console through a browser).
    project = source.Project(project_id)
    if not project.GetRepo(args.src):
      message = ('Repository "{src}" in project "{prj}" does not yet '
                 'exist.'.format(src=args.src, prj=project_id))
      prompt_string = 'Would you like to create it'
      if args.autocreate or console_io.PromptContinue(
          message=message, prompt_string=prompt_string, default=True):
        try:
          project.CreateRepo(args.src)
        except exceptions.HttpError as e:
          message = ('Failed to create repository [{src}] for Project '
                     '[{prj}] with error [{err}]. Please retry with:\n'
                     '  $ gcloud alpha source repos create {src}\n'.format(
                         prj=project_id, err=e, src=args.src))
          raise source.RepoCreationError(message=message)
      else:
        message = ('Cannot clone from a non-existent repo. Please create it '
                   'with:\n  $ gcloud alpha source repos create {src}\n and '
                   'try cloning again.'.format(src=args.src))
        raise source.RepoNoExistError(message=message)
    project_repo = git.Git(project_id, args.src)
    path = project_repo.Clone(destination_path=args.dst or args.src,
                              dry_run=args.dry_run)
    if path and not args.dry_run:
      log.status.write('Project [{prj}] repository [{repo}] was cloned to '
                       '[{path}].\n'.format(prj=project_id, path=path,
                                            repo=project_repo.GetName()))
