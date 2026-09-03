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
"""Command to update a Cloud FTP server."""

from googlecloudsdk.api_lib.storage import ftp_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage.ftp import operations_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.Command):
  """Update an existing Cloud FTP server."""

  hints = base.CommandHint(read_only=False)

  detailed_help = {
      'DESCRIPTION': (
          """\
          Update an existing Cloud FTP server.
      """
      ),
      'EXAMPLES': (
          """\
          To update display name of server `my-server` in `us-west1`, run:

            $ {command} my-server --location=us-west1 --display-name="New Name"
      """
      ),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'SERVER_ID',
        help='The ID of the FTP server to update.',
    )

    parser.add_argument(
        '--location',
        required=True,
        help='The region of the server.',
    )
    parser.add_argument(
        '--display-name',
        help='Update the display name.',
    )
    parser.add_argument(
        '--allowed-cidr-blocks',
        type=arg_parsers.ArgList(),
        metavar='CIDR_BLOCK',
        help='Update the list of allowed CIDR blocks (overwrites existing).',
    )
    parser.add_argument(
        '--consumer-accept-list',
        type=arg_parsers.ArgDict(value_type=int),
        metavar='PROJECT_ID=LIMIT',
        help='Update the PSC allow list (overwrites existing).',
    )
    parser.add_argument(
        '--consumer-reject-list',
        type=arg_parsers.ArgList(),
        metavar='PROJECT_ID',
        help='Update the PSC reject list (overwrites existing).',
    )

  def Run(self, args):
    client = ftp_api.FtpApi()
    existing_server = client.GetServer(args.location, args.SERVER_ID)
    access_type_enum = client.messages.Server.AccessTypeValueValuesEnum

    is_internal = existing_server.accessType == access_type_enum.INTERNAL
    is_external = existing_server.accessType == access_type_enum.EXTERNAL

    if is_internal and args.IsSpecified('allowed_cidr_blocks'):
      raise exceptions.Error(
          '--allowed-cidr-blocks cannot be used with servers of access type '
          'INTERNAL.'
      )
    if is_external and args.IsSpecified('consumer_accept_list'):
      raise exceptions.Error(
          '--consumer-accept-list cannot be used with servers of access '
          'type EXTERNAL.'
      )
    if is_external and args.IsSpecified('consumer_reject_list'):
      raise exceptions.Error(
          '--consumer-reject-list cannot be used with servers of access '
          'type EXTERNAL.'
      )

    if (
        args.IsSpecified('allowed_cidr_blocks')
        or args.IsSpecified('consumer_accept_list')
        or args.IsSpecified('consumer_reject_list')
    ):
      log.warning(
          'Provided lists will overwrite existing server configuration.'
      )

    kwargs = {}
    if args.IsSpecified('display_name'):
      kwargs['display_name'] = args.display_name
    if args.IsSpecified('allowed_cidr_blocks'):
      kwargs['allowed_cidr_blocks'] = args.allowed_cidr_blocks
    if args.IsSpecified('consumer_accept_list'):
      kwargs['consumer_accept_list'] = args.consumer_accept_list
    if args.IsSpecified('consumer_reject_list'):
      kwargs['consumer_reject_list'] = args.consumer_reject_list

    op = client.UpdateServer(
        args.location, args.SERVER_ID, existing_server=existing_server, **kwargs
    )

    op_ref = operations_util.GetOperationRef(op.name)
    return client.WaitForOperation(
        op_ref,
        'Waiting for server [{}] to be updated'.format(args.SERVER_ID),
        result_service=client.servers_service,
    )
