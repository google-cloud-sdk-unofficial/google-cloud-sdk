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

"""A command to install Application Default Credentials using a user account."""

import textwrap

from googlecloudsdk.api_lib.auth import util as auth_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import gce as c_gce
from googlecloudsdk.core.credentials import store as c_store
from oauth2client import client


class Login(base.Command):
  """Authorize Application Default Credentials to access Google Cloud Platform.

  Obtains user access credentials via a web flow for the Google Cloud Platform
  resources of the given account, and puts them in the well-known location for
  Application Default Credentials to use them as a proxy for a service account.

  This command is useful for when you are developing code that would normally
  use a service account, but you need to run the code in a local development
  environment, and it is easier to provide user credentials.
  These user credentials will then be used as a "proxy" for an associated
  service account. The credentials will apply to all projects accessed through
  Application Default Credentials. This command has no effect on the user
  account(s) used with the 'gcloud auth login' command, but any existing
  credentials previously installed by this command (or
  'gcloud auth application-default activate-service-account') will be
  overwritten.
  """

  @staticmethod
  def Args(parser):
    """Set args for gcloud auth application-default login."""

    parser.add_argument(
        '--launch-browser',
        action='store_true', default=True, dest='launch_browser',
        help='Launch a browser for authorization. If not enabled or DISPLAY '
        'variable is not set, prints a URL to standard output to be copied.')
    parser.add_argument(
        '--brief', action='store_true',
        help='Minimal user output.')
    parser.add_argument(
        '--client-id-file',
        help='A file containing a client id.')
    parser.add_argument(
        '--scopes',
        type=arg_parsers.ArgList(min_length=1),
        action=arg_parsers.FloatingListValuesCatcher(),
        help='The names of the scopes to authorize for.')

  def Format(self, unused_args):
    return None

  @c_exc.RaiseToolExceptionInsteadOf(c_store.Error)
  def Run(self, args):
    """Run the authentication command."""

    if c_gce.Metadata().connected:
      message = textwrap.dedent("""
          You are running on a Google Compute Engine virtual machine.
          The service credentials associated with this virtual machine
          will automatically be used by Application Default
          Credentials, so it is not necessary to use this command.

          If you decide to proceed anyway, your user credentials may be visible
          to others with access to this virtual machine. Are you sure you want
          to authenticate with your personal account?
          """)
      answer = console_io.PromptContinue(message=message)
      if not answer:
        return None

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

    scopes = args.scopes
    if not scopes:
      scopes = [auth_util.CLOUD_PLATFORM_SCOPE]

    launch_browser = auth_util.ShouldLaunchBrowser(args.launch_browser)
    creds = auth_util.DoInstalledAppBrowserFlow(
        client_id_file=args.client_id_file,
        scopes=scopes,
        launch_browser=launch_browser)
    return self.SaveCredentials(creds, args.brief)

  def SaveCredentials(self, creds, brief):
    """Saves the credentials in the well-known file for ADC."""
    google_creds = client.GoogleCredentials(
        creds.access_token, creds.client_id, creds.client_secret,
        creds.refresh_token, creds.token_expiry, creds.token_uri,
        creds.user_agent, creds.revoke_uri)
    try:
      auth_util.CreateWellKnownFileDir()
      client.save_to_well_known_file(google_creds)
    except IOError as e:
      raise c_exc.ToolException(
          'error saving Application Default Credentials: ' + str(e))
    if not brief:
      log.status.write(
          '\nApplication Default Credentials are now saved, and will\n'
          'use the provided account.\n')
      log.status.write(
          '\nThis does not affect any credentials that you may have\n'
          'set up for the Google Cloud SDK.\n')
    return creds
