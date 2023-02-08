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

from apitools.base.py import exceptions
from apitools.base.py import transfer

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import flags
from googlecloudsdk.command_lib.artifacts import requests
from googlecloudsdk.core import log
from googlecloudsdk.core.credentials import transports


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
    log.status.Print('Downloading the file.')
    client = requests.GetClientV1beta2()
    repo_ref = args.CONCEPTS.repository.Parse()
    file_name = args.name
    file_id = '{}:{}:{}'.format(args.package, args.version, file_name)
    file_path = os.path.join(args.destination, file_name)

    if os.path.exists(file_path):
      raise exceptions.InvalidUserInputError(
          'File {} already exists.'.format(file_path)
      )

    request = (
        requests.GetMessagesV1beta2().ArtifactregistryMediaDownloadRequest(
            name='{}/files/{}'.format(repo_ref.RelativeName(), file_id)
        )
    )
    # Allow overwrites in /tmp
    download_object = transfer.Download.FromFile(
        os.path.join(tempfile.gettempdir(), file_name), True
    )
    download_object.bytes_http = transports.GetApitoolsTransport(
        response_encoding=None
    )

    try:
      client.media.Download(request, download=download_object)
    except exceptions.HttpError as err:
      # If an exception was raised, we do not move the file.
      raise err

    finally:
      download_object.stream.close()

    try:
      # Only move the file to the user specified path if no exception occured.
      os.rename(os.path.join(tempfile.gettempdir(), file_name), file_path)
    except OSError as err:
      raise err

    log.status.Print('Successfully downloaded the file to ' + args.destination)
