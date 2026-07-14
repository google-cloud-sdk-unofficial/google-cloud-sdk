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
"""Command to update a Cloud FTP user."""

from googlecloudsdk.api_lib.storage import ftp
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage.ftp import operations_util
from googlecloudsdk.command_lib.storage.ftp import users_util
from googlecloudsdk.core import log


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.Command):
  """Update an existing Cloud FTP user."""

  hints = base.CommandHint(read_only=False)

  detailed_help = {
      'DESCRIPTION': (
          """\
          Update an existing Cloud FTP user.
      """
      ),
      'EXAMPLES': (
          """\
          To update service account of user `my-user` for server `my-server` in `us-west1`, run:

            $ {command} my-user --server=my-server --location=us-west1 --customer-service-account=new-sa@my-project.iam.gserviceaccount.com
      """
      ),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'USER_ID',
        help='The ID of the user to update.',
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
        '--customer-service-account',
        help='The service account email associated with this user.',
    )
    parser.add_argument(
        '--user-credentials-from-file',
        type=arg_parsers.FileContents(),
        help='Path to a JSON file containing user credentials.',
    )
    parser.add_argument(
        '--storage-directory-mapping',
        type=arg_parsers.ArgDict(
            spec={
                'bucket': str,
                'bucket_prefix': str,
                'directory': str,
                'permission': str,
            },
            required_keys=['bucket', 'directory', 'permission'],
        ),
        action='append',
        metavar='PROPERTY=VALUE',
        help='Mapping of Google Cloud Storage bucket to virtual directory.',
    )

  def Run(self, args):
    client = ftp.FtpClient()
    user_name = users_util.GetUserResourceName(
        args.location, args.server, args.USER_ID
    )
    existing_user = client.GetUser(user_name)

    if args.IsSpecified('user_credentials_from_file') or args.IsSpecified(
        'storage_directory_mapping'
    ):
      log.warning('Provided lists will overwrite existing user configuration.')

    user_msg, update_mask = users_util.UpdateUserMsg(
        client.messages, args, existing_user
    )

    op = client.UpdateUser(user_msg, update_mask)

    if args.async_:
      log.status.Print('Update request issued for: [{}]'.format(args.USER_ID))
      log.status.Print('Check operation [{}] for status.'.format(op.name))
      return op

    op_ref = operations_util.GetOperationRef(op.name)
    return operations_util.WaitForOperation(
        op_ref,
        'Waiting for user [{}] to be updated'.format(args.USER_ID),
        result_service=client.users_service,
    )
