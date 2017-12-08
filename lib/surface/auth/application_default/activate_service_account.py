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

"""A command to install ADC using a service account."""

import json
import textwrap

from googlecloudsdk.api_lib.auth import util as auth_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import service_account
from googlecloudsdk.core.credentials import store as c_store
from oauth2client import client


class ActivateServiceAccount(base.Command):
  """Authorize access to Google Cloud Platform using a service account.

  Gets credentials for a service account, using a .json file
  for the private key, and puts them in the well-known location for
  Application Default Credentials.
  The --project option is ignored.

  This command has no effect on the service account(s) used with the
  'gcloud auth activate-service-account' command, but any existing credentials
  previously installed by this command (or
  'gcloud auth application-default login') will be overwritten.
  """

  @staticmethod
  def Args(parser):
    """Set args for gcloud auth application-default activate-service-account."""
    parser.add_argument('--key-file',
                        help=('Path to the private key file.'),
                        required=True)
    parser.add_argument(
        '--brief', action='store_true',
        help='Minimal user output.')

  @c_exc.RaiseToolExceptionInsteadOf(c_store.Error)
  def Run(self, args):
    """Create service account credentials."""

    if auth_util.AdcEnvVariableIsSet():
      message = textwrap.dedent("""
          The environment variable GOOGLE_APPLICATION_CREDENTIALS is set,
          which means that the file pointed to by that variable will be used
          instead of any credentials set up with this command. Do you want to
          continue anyway?
          """)
      answer = console_io.PromptContinue(message=message)
      if not answer:
        return None

    json_key = self.LoadKeyFile(args.key_file)

    try:
      cred = service_account.ServiceAccountCredentials(
          service_account_id=json_key['client_id'],
          service_account_email=json_key['client_email'],
          private_key_id=json_key['private_key_id'],
          private_key_pkcs8_text=json_key['private_key'],
          scopes=[],
          user_agent=config.CLOUDSDK_USER_AGENT)
    except KeyError:
      raise c_exc.ToolException('The .json key file is not in a valid format.')

    self.SaveCredentials(cred, args.brief)

    log.status.Print('Activated service account credentials for: [{0}]'
                     .format(json_key['client_email']))
    return cred

  def LoadKeyFile(self, key_file):
    try:
      private_key = open(key_file, 'rb').read()
    except IOError as e:
      raise c_exc.BadFileException(e)

    try:
      return json.loads(private_key)
    except ValueError:
      raise c_exc.ToolException('The .json key file is not in a valid format.')

  def SaveCredentials(self, creds, brief):
    """Saves the credentials in the well-known file for ADC."""
    try:
      client.save_to_well_known_file(creds)
    except IOError as e:
      raise c_exc.ToolException(
          'Error saving Application Default Credentials: ' + str(e))

    if not brief:
      log.status.write(
          '\nApplication Default Credentials are now saved, and will\n'
          'use the given service account.\n')
      log.status.write(
          '\nThis does not affect any credentials that you may have\n'
          'set up for the Google Cloud SDK.\n')

    return creds

  def Format(self, unused_args):
    return 'none'
