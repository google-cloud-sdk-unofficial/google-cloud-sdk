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

from apitools.base.py import transfer
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.artifacts import flags
from googlecloudsdk.command_lib.artifacts import requests
from googlecloudsdk.core import log


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
    file = args.CONCEPTS.file.Parse()
    download_path = args.destination
    request = requests.GetMessagesV1beta2(
    ).ArtifactregistryMediaDownloadRequest(name=file.RelativeName())
    download_object = transfer.Download.FromFile(
        download_path + '/' + file.filesId, args.allow_overwrite)
    client.media.Download(request, download=download_object)
    log.status.Print(
        'Successfully downloaded the file to ' + download_path)
