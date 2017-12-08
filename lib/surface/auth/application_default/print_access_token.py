# Copyright 2016 Google Inc. All Rights Reserved.
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

"""A command that prints an access token for Application Default Credentials.
"""

from googlecloudsdk.api_lib.auth import util as auth_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import log
from googlecloudsdk.core.credentials import store as c_store
from oauth2client import client


class PrintAccessToken(base.Command):
  """Print an access token for the active credentials.

  The scopes argument is only used for service account credentials, because
  user credentials will already be bound to a scope. The scopes argument
  is simply ignored for user credentials. If it is not provided when service
  account credentials are used, then it is defaulted to
  'https://www.googleapis.com/auth/cloud-platform'.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--scopes',
        type=arg_parsers.ArgList(min_length=1),
        action=arg_parsers.FloatingListValuesCatcher(),
        help='The names of the scopes to print an access token for.')

  @c_exc.RaiseToolExceptionInsteadOf(c_store.Error)
  def Run(self, args):
    """Run the helper command."""

    creds = client.GoogleCredentials.get_application_default()

    if creds.create_scoped_required():
      scopes = args.scopes
      if not scopes:
        scopes = [auth_util.CLOUD_PLATFORM_SCOPE]

      creds = creds.create_scoped(scopes)
      log.status.Print('creds = ' + str(creds))

    access_token_info = creds.get_access_token()
    if not access_token_info:
      raise c_exc.ToolException(
          'No access token could be obtained from the current credentials.')

    return access_token_info

  def Format(self, unused_args):
    return 'value(access_token)'
