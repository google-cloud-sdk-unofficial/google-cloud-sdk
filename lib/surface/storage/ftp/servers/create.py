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
"""Command to create a Cloud FTP server."""

from googlecloudsdk.api_lib.storage import ftp_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage.ftp import operations_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Create a new Cloud FTP server."""

  hints = base.CommandHint(read_only=False)

  detailed_help = {
      'DESCRIPTION': (
          """\
          Create a new Cloud FTP server.
      """
      ),
      'EXAMPLES': (
          """\
          To create an EXTERNAL server `my-server` in `us-west1`, run:

            $ {command} my-server --location=us-west1 --access-type=EXTERNAL --allowed-cidr-blocks=0.0.0.0/0
      """
      ),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'SERVER_ID',
        help='The ID of the FTP server to create.',
    )

    parser.add_argument(
        '--location',
        required=True,
        help='The region where the server will be created.',
    )
    parser.add_argument(
        '--display-name',
        help='An optional display name for the server.',
    )
    parser.add_argument(
        '--access-type',
        required=True,
        choices=['EXTERNAL', 'INTERNAL'],
        help='The type of access for the server.',
    )
    parser.add_argument(
        '--allowed-cidr-blocks',
        type=arg_parsers.ArgList(),
        metavar='CIDR_BLOCK',
        help=(
            '(Required for EXTERNAL servers) A comma-separated list of CIDR'
            ' blocks allowed to connect.'
        ),
    )
    parser.add_argument(
        '--consumer-accept-list',
        type=arg_parsers.ArgDict(value_type=int),
        metavar='PROJECT_ID=LIMIT',
        help=(
            '(Required for INTERNAL servers) A comma-separated list of projects'
            ' allowed to connect via PSC.'
        ),
    )
    parser.add_argument(
        '--consumer-reject-list',
        type=arg_parsers.ArgList(),
        metavar='PROJECT_ID',
        help=(
            '(For INTERNAL servers) A comma-separated list of projects denied'
            ' connection via PSC.'
        ),
    )
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    client = ftp_api.FtpApi()

    if args.access_type.upper() == 'EXTERNAL' and not args.allowed_cidr_blocks:
      raise exceptions.Error(
          '--allowed-cidr-blocks is required for EXTERNAL access type.'
      )
    if args.access_type.upper() == 'INTERNAL' and not args.consumer_accept_list:
      raise exceptions.Error(
          '--consumer-accept-list is required for INTERNAL access type.'
      )

    op = client.CreateServer(
        args.location,
        args.SERVER_ID,
        display_name=args.display_name,
        access_type=args.access_type,
        allowed_cidr_blocks=args.allowed_cidr_blocks,
        consumer_accept_list=args.consumer_accept_list,
        consumer_reject_list=args.consumer_reject_list,
        labels=args.labels,
    )

    op_ref = operations_util.GetOperationRef(op.name)
    return client.WaitForOperation(
        op_ref,
        'Waiting for server [{}] to be created'.format(args.SERVER_ID),
        result_service=client.servers_service,
    )
