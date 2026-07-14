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
"""Command to describe a Cloud FTP operation."""

from googlecloudsdk.api_lib.storage import ftp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage.ftp import servers_util


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """A command that gets details about a specific Cloud FTP operation."""

  hints = base.CommandHint(read_only=True)

  detailed_help = {
      'DESCRIPTION': (
          """\
          Get details about a specific Cloud FTP long-running operation.
      """
      ),
      'EXAMPLES': (
          """\
          To describe operation `op-123` in location `us-west1`, run:

            $ {command} op-123 --location=us-west1
      """
      ),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'operation_id',
        help='The ID of the operation to describe.',
    )
    parser.add_argument(
        '--location',
        required=True,
        help='The region of the operation.',
    )

  def Run(self, args):
    client = ftp.FtpClient()
    parent = servers_util.GetParentString(args.location)
    operation_name = '{}/operations/{}'.format(parent, args.operation_id)
    return client.GetOperation(operation_name)
