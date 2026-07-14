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
"""Command to delete a Cloud FTP user."""

from googlecloudsdk.api_lib.storage import ftp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage.ftp import operations_util
from googlecloudsdk.command_lib.storage.ftp import users_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.Command):
  """Delete a Cloud FTP user."""

  hints = base.CommandHint(read_only=False)

  detailed_help = {
      'DESCRIPTION': (
          """\
          Delete a Cloud FTP user.
      """
      ),
      'EXAMPLES': (
          """\
          To delete user `my-user` for server `my-server` in `us-west1`, run:

            $ {command} my-user --server=my-server --location=us-west1
      """
      ),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'USER_ID',
        help='The ID of the user to delete.',
    )
    parser.add_argument(
        '--async',
        action='store_true',
        dest='async_',
        help=(
            'Return immediately, without waiting for the operation to complete.'
        ),
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
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force deletion without confirmation prompt.',
    )

  def Run(self, args):
    if not args.force:
      console_io.PromptContinue(
          message='Are you sure you want to delete user [{}]?'.format(
              args.USER_ID
          ),
          cancel_on_no=True,
      )

    client = ftp.FtpClient()
    user_name = users_util.GetUserResourceName(
        args.location, args.server, args.USER_ID
    )

    op = client.DeleteUser(user_name, force=args.force)

    if args.async_:
      log.status.Print('Delete request issued for: [{}]'.format(args.USER_ID))
      log.status.Print('Check operation [{}] for status.'.format(op.name))
      return op

    op_ref = operations_util.GetOperationRef(op.name)
    return operations_util.WaitForOperation(
        op_ref,
        'Waiting for user [{}] to be deleted'.format(args.USER_ID),
        result_service=None,
    )
