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
"""Implements the command to download generic artifacts from a repository."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import tempfile

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import download_util
from googlecloudsdk.command_lib.artifacts import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
@base.Hidden
class Download(base.Command):
  """Download a generic artifact from a generic artifact repository."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
    To download version v0.1.0 of myfile.txt located in a repository in "us-central1" to /path/to/destination/:

        $ {command} --location=us-central1 --project=myproject --repository=myrepo \
          --package=mypackage --version=v0.1.0 --destination=/path/to/destination/ \
          --name=myfile.txt
    """,
  }

  @staticmethod
  def Args(parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    flags.GetRequiredRepoFlag().AddToParser(parser)

    parser.add_argument(
        '--destination',
        metavar='DESTINATION',
        required=True,
        help='The path where you want to save the downloaded file.',
    )
    parser.add_argument(
        '--package',
        metavar='ARTIFACT',
        required=True,
        help='The artifact to download.',
    )
    parser.add_argument(
        '--version',
        metavar='VERSION',
        required=True,
        help='The version of the artifact to download.',
    )
    parser.add_argument(
        '--name',
        metavar='NAME',
        required=True,
        help='The name of the artifact to download.'
    )

  def Run(self, args):
    """Run the generic artifact download command."""

    repo_ref = args.CONCEPTS.repository.Parse()
    file_id = '{}:{}:{}'.format(args.package, args.version, args.name)
    tmp_path = os.path.join(tempfile.gettempdir(), args.name)
    final_path = os.path.join(args.destination, args.name)
    file_res_name = '{}/files/{}'.format(repo_ref.RelativeName(), file_id)

    download_util.Download(tmp_path, final_path, file_res_name, False)
    log.status.Print(
        'Successfully downloaded the file to {}'.format(args.destination)
    )
