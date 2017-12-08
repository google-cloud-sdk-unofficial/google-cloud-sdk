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
import json
import os

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import service_account
from googlecloudsdk.core.credentials import store as c_store
from oauth2client import client


class ActivateServiceAccount(base.Command):
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
      private_key = open(args.key_file, 'rb').read()
    except IOError as e:
      raise c_exc.BadFileException(e)

    json_key = None
    try:
      json_key = json.loads(private_key)
    except ValueError:
      pass

    account = None
    if json_key:
      if args.password_file or args.prompt_for_password:
        raise c_exc.InvalidArgumentException(
            '--password-file',
            'A .json service account key does not require a password.')
      account = json_key.get('client_email', None)
      if not account:
        raise c_exc.ToolException(
            'The .json key file is not in a valid format.')
      if args.account and args.account != account:
        raise c_exc.InvalidArgumentException(
            'ACCOUNT',
            'The given account name does not match the account name in the key '
            'file.  This argument can be omitted when using .json keys.')
      cred = service_account.ServiceAccountCredentials(
          service_account_id=json_key['client_id'],
          service_account_email=json_key['client_email'],
          private_key_id=json_key['private_key_id'],
          private_key_pkcs8_text=json_key['private_key'],
          scopes=config.CLOUDSDK_SCOPES,
          user_agent=config.CLOUDSDK_USER_AGENT)
    else:
      account = args.account
      if not account:
        raise c_exc.RequiredArgumentException(
            'ACCOUNT', 'An account is required when using .p12 keys')
      password = None
      if args.password_file:
        try:
          password = open(args.password_file).read().strip()
        except IOError as e:
          raise c_exc.UnknownArgumentException('--password-file', e)
      if args.prompt_for_password:
        password = getpass.getpass('Password: ')

      if not client.HAS_CRYPTO:
        if not os.environ.get('CLOUDSDK_PYTHON_SITEPACKAGES'):
          raise c_exc.ToolException(
              ('PyOpenSSL is not available. If you have already installed '
               'PyOpenSSL, you will need to enable site packages by '
               'setting the environment variable CLOUDSDK_PYTHON_SITEPACKAGES '
               'to 1. If that does not work, see '
               'https://developers.google.com/cloud/sdk/crypto for details.'))
        else:
          raise c_exc.ToolException(
              ('PyOpenSSL is not available. See '
               'https://developers.google.com/cloud/sdk/crypto for details.'))

      if password:
        cred = client.SignedJwtAssertionCredentials(
            service_account_name=account,
            private_key=private_key,
            scope=config.CLOUDSDK_SCOPES,
            private_key_password=password,
            user_agent=config.CLOUDSDK_USER_AGENT)
      else:
        cred = client.SignedJwtAssertionCredentials(
            service_account_name=account,
            private_key=private_key,
            scope=config.CLOUDSDK_SCOPES,
            user_agent=config.CLOUDSDK_USER_AGENT)
      try:
        c_store.Refresh(cred)
      except c_store.TokenRefreshError as e:
        log.file_only_logger.exception(e)
        raise c_exc.ToolException(
            'Failed to activate the given service account.  Please ensure the '
            'key is valid and that you have provided the correct account name.')

    c_store.Store(cred, account)

    properties.PersistProperty(properties.VALUES.core.account, account)

    project = args.project
    if project:
      properties.PersistProperty(properties.VALUES.core.project, project)

    log.status.Print('Activated service account credentials for: [{0}]'
                     .format(account))
    return cred

  def Format(self, unused_args):
    return 'none'
