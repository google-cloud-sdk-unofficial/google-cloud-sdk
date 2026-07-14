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
"""Command to describe a Cloud FTP user."""

from googlecloudsdk.api_lib.storage import ftp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage.ftp import users_util


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe an existing Cloud FTP user."""

  hints = base.CommandHint(read_only=True)

  detailed_help = {
      'DESCRIPTION': (
          """\
          Describe an existing Cloud FTP user.
      """
      ),
      'EXAMPLES': (
          """\
          To describe user `my-user` for server `my-server` in `us-west1`, run:

            $ {command} my-user --server=my-server --location=us-west1
      """
      ),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'USER_ID',
        help='The ID of the user to describe.',
    )
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

  def Run(self, args):
    client = ftp.FtpClient()
    user_name = users_util.GetUserResourceName(
        args.location, args.server, args.USER_ID
    )
    return client.GetUser(user_name)
