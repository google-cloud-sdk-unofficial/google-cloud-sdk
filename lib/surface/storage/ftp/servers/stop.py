# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Command to stop a Cloud FTP server."""

from googlecloudsdk.api_lib.storage import ftp_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage.ftp import operations_util


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Stop(base.Command):
  """Stop a Cloud FTP server."""

  hints = base.CommandHint(read_only=False)

  detailed_help = {
      'DESCRIPTION': (
          """\
          Stop a Cloud FTP server.
      """
      ),
      'EXAMPLES': (
          """\
          To stop server `my-server` in `us-west1`, run:

            $ {command} my-server --location=us-west1
      """
      ),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'SERVER_ID',
        help='The ID of the FTP server to stop.',
    )

    parser.add_argument(
        '--location',
        required=True,
        help='The region of the server.',
    )

  def Run(self, args):
    client = ftp_api.FtpApi()
    op = client.StopServer(args.location, args.SERVER_ID)

    op_ref = operations_util.GetOperationRef(op.name)
    return client.WaitForOperation(
        op_ref,
        'Waiting for server [{}] to stop'.format(args.SERVER_ID),
        result_service=client.servers_service,
    )

