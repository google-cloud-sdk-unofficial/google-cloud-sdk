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
"""Command to list Cloud FTP users."""

from googlecloudsdk.api_lib.storage import ftp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage.ftp import servers_util


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Cloud FTP users."""

  hints = base.CommandHint(read_only=True)

  detailed_help = {
      'DESCRIPTION': (
          """\
          List all Cloud FTP users for a specific server.
      """
      ),
      'EXAMPLES': (
          """\
          To list users for server `my-server` in `us-west1`, run:

            $ {command} --server=my-server --location=us-west1
      """
      ),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--server',
        required=True,
        help='The ID of the server.',
    )
    parser.add_argument(
        '--location',
        required=True,
        help='The region of the server.',
    )
    parser.display_info.AddFormat("""\
        table(
            name.basename():label=NAME,
            username:label=USERNAME,
            customerServiceAccount:label=SERVICE_ACCOUNT,
            state:label=STATE
        )
    """)

  def Run(self, args):
    client = ftp.FtpClient()
    parent = servers_util.GetServerResourceName(args.location, args.server)
    return client.ListUsers(parent, page_size=args.page_size, limit=args.limit)
