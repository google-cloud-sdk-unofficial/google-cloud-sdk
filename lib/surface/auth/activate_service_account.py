# Copyright 2013 Google Inc. All Rights Reserved.
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

"""A simple auth command to bootstrap authentication with oauth2."""

import getpass

from googlecloudsdk.api_lib.auth import service_account as auth_service_account
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store as c_store


class ActivateServiceAccount(base.SilentCommand):
  """Authorize access to Google Cloud Platform using a service account.

  Obtains access credentials for the service account using a .json (preferred)
  or .p12 file that contains a private authorization key. You obtain the key
  file from the [Cloud Platform console](https://console.cloud.google.com). For
  .p12 files, a password is required. This password is displayed in the console
  when you create the key. If you specify a project using the `--project` flag,
  the project is set in your active configuration.

  Any previously active credentials will still be retained,
  they will just no longer be the active credentials.
  """

  @staticmethod
  def Args(parser):
    """Set args for serviceauth."""
    parser.add_argument('account', nargs='?',
                        help='E-mail address of the service account.')
    parser.add_argument('--key-file',
                        help=('Path to the private key file.'),
                        required=True)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--password-file',
                       help=('Path to a file containing the password for the '
                             'service account private key '
                             '(only for a .p12 file).'))
    group.add_argument('--prompt-for-password', action='store_true',
                       help=('Prompt for the password for the service account '
                             'private key (only for a .p12 file).'))

  def Run(self, args):
    """Create service account credentials."""

    try:
      cred = auth_service_account.CredentialsFromAdcFile(args.key_file)
    except auth_service_account.BadCredentialFileException:
      account = args.account
      if not account:
        raise c_exc.RequiredArgumentException(
            'ACCOUNT', 'An account is required when using .p12 keys')
      password = None
      if args.password_file:
        try:
          with open(args.password_file) as f:
            password = f.read().strip()
        except IOError as e:
          raise c_exc.UnknownArgumentException('--password-file', e)
      elif args.prompt_for_password:
        password = getpass.getpass('Password: ')

      cred = auth_service_account.CredentialsFromP12File(
          args.key_file, account, password=password)
    else:  # JSON format key file.
      if args.password_file or args.prompt_for_password:
        raise c_exc.InvalidArgumentException(
            '--password-file',
            'A .json service account key does not require a password.')
      account = cred.service_account_email
      if args.account and args.account != account:
        raise c_exc.InvalidArgumentException(
            'ACCOUNT',
            'The given account name does not match the account name in the key '
            'file.  This argument can be omitted when using .json keys.')

    try:
      c_store.ActivateCredentials(account, cred)
    except c_store.TokenRefreshError as e:
      log.file_only_logger.exception(e)
      raise auth_service_account.BadCredentialFileException(
          'Failed to activate the given service account. '
          'Please ensure provided key file is valid.')

    project = args.project
    if project:
      properties.PersistProperty(properties.VALUES.core.project, project)

    log.status.Print('Activated service account credentials for: [{0}]'
                     .format(account))

