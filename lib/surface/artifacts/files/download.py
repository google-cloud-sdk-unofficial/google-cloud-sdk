# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Download Artifact Registry files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import shutil
import tempfile

from apitools.base.py import exceptions
from apitools.base.py import transfer
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import flags
from googlecloudsdk.command_lib.artifacts import requests
from googlecloudsdk.command_lib.artifacts import util
from googlecloudsdk.core import log
from googlecloudsdk.core.credentials import transports


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.Hidden
class Download(base.Command):
  """Download an Artifact Registry file.

  Downloads an Artifact Registry file based on file name.

  """

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
      To download a file named `myfile` in project `my-project` under repository `my-repo` in `us-central1` to the local path `~/`:

          $ {command} --location=us-central1 --project=my-project --repository=my-repo --destination=~/ myfile

      To download a file named `myfile` in project `my-project` under repository `my-repo` in `us-central1` to the local path `~/` with file overwriting enabled:

          $ {command} --location=us-central1 --project=my-project --repository=my-repo --destination=~/ myfile --allow-overwrite
    """,
  }

  @staticmethod
  def Args(parser):
    flags.GetRequiredFileFlag().AddToParser(parser)
    flags.GetAllowOverwriteFlag().AddToParser(parser)
    parser.add_argument(
        '--destination',
        metavar='DESTINATION',
        required=True,
        help="""\
            The path where you want to download the file.""")

  def Run(self, args):
    """Run the file download command."""
    log.status.Print('Downloading the file.')
    client = requests.GetClientV1beta2()

    # Escape all slashes in the file name so they are not seen as directories.
    file_escaped = util.EscapeFileNameName(args.CONCEPTS.file.Parse())
    file_path = os.path.join(args.destination, file_escaped.filesId)

    request = requests.GetMessagesV1beta2(
    ).ArtifactregistryMediaDownloadRequest(name=file_escaped.RelativeName())

    # Only move the file to the user specified path if overwrites are allowed.
    if (os.path.exists(file_path) and not args.allow_overwrite):
      raise exceptions.InvalidUserInputError(
          'File %s exists and overwrite not specified.' % file_path
      )
    # Allow overwrites in /tmp
    download_object = transfer.Download.FromFile(
        os.path.join(tempfile.gettempdir(), file_escaped.filesId), True
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
      shutil.move(
          os.path.join(tempfile.gettempdir(), file_escaped.filesId), file_path
      )
    except OSError as err:
      raise err

    log.status.Print(
        'Successfully downloaded the file to ' + args.destination)
