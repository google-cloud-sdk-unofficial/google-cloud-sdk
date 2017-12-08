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

"""The auth command gets tokens via oauth2."""

import argparse
import textwrap

from googlecloudsdk.api_lib.auth import util as auth_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import devshell as c_devshell
from googlecloudsdk.core.credentials import gce as c_gce
from googlecloudsdk.core.credentials import store as c_store
from oauth2client import client


class Login(base.Command):
  """Authorize gcloud to access Google Cloud Platform.

  Obtains access credentials for your user account via a web-based authorization
  flow. When this command completes successfully, it sets the active account
  in the current configuration to the account specified. If no configuration
  exists, it creates a configuration named default.

  If valid credentials for an account are already available from a prior
  authorization, the account is set to active without rerunning the flow.

  Use `gcloud auth list` to view credentialed accounts.

  Deprecated behavior: This command also saves the credentials for
  Application Default Credentials. This behavior has been taken over by
  'gcloud auth application-default login', so prefer to use that command
  instead for that purpose.
  """

  @staticmethod
  def Args(parser):
    """Set args for gcloud auth."""

    parser.add_argument(
        '--launch-browser',
        action='store_true', default=True, dest='launch_browser',
        help='Launch a browser for authorization. If not enabled or DISPLAY '
        'variable is not set, prints a URL to standard output to be copied.')
    parser.add_argument(
        '--activate', action='store_true', default=True,
        help='Set the new account to active.')
    # --do-not-activate for (hidden) backwards compatibility.
    parser.add_argument(
        '--do-not-activate', action='store_false', dest='activate',
        help=argparse.SUPPRESS)
    parser.add_argument(
        '--brief', action='store_true',
        help='Minimal user output.')
    parser.add_argument(
        '--force', action='store_true',
        help='Re-run the web authorization flow even if the given account has '
        'valid credentials.')
    parser.add_argument(
        '--enable-gdrive-access', action='store_true',
        help='Enable Google Drive access.')
    parser.add_argument(
        'account', nargs='?', help='User account used for authorization.')

  def Format(self, unused_args):
    return None

  @c_exc.RaiseToolExceptionInsteadOf(c_store.Error)
  def Run(self, args):
    """Run the authentication command."""

    scopes = None
    if args.enable_gdrive_access:
      scopes = config.CLOUDSDK_SCOPES
      scopes += (auth_util.GOOGLE_DRIVE_SCOPE,)

    if c_devshell.IsDevshellEnvironment():
      message = """
          You are already authenticated with gcloud when running
          inside the Cloud Shell and so do not need to run this
          command.

          Do you wish to proceed anyway?
        """
      answer = console_io.PromptContinue(message=message)
      if not answer:
        return None
    elif c_gce.Metadata().connected:
      message = textwrap.dedent("""
          You are running on a Google Compute Engine virtual machine.
          It is recommended that you use service accounts for authentication.

          You can run:

            $ gcloud config set account `ACCOUNT`

          to switch accounts if necessary.

          Your credentials may be visible to others with access to this
          virtual machine. Are you sure you want to authenticate with
          your personal account?
          """)
      answer = console_io.PromptContinue(message=message)
      if not answer:
        return None

    account = args.account

    if account and not args.force:
      creds = c_store.LoadIfValid(account=account, scopes=scopes)
      if creds:
        # Account already has valid creds, just switch to it.
        return self.LoginAs(account, creds, args.project, args.activate,
                            args.brief)

    # No valid creds, do the web flow.
    launch_browser = auth_util.ShouldLaunchBrowser(args.launch_browser)
    creds = self.DoInstalledAppBrowserFlow(launch_browser, scopes)
    web_flow_account = creds.id_token['email']
    if account and account.lower() != web_flow_account.lower():
      raise c_exc.ToolException(
          'You attempted to log in as account [{account}] but the received '
          'credentials were for account [{web_flow_account}].\n\n'
          'Please check that your browser is logged in as account [{account}] '
          'and that you are using the correct browser profile.'.format(
              account=account, web_flow_account=web_flow_account))

    account = web_flow_account
    # We got new creds, and they are for the correct user.
    c_store.Store(creds, account, scopes)
    return self.LoginAs(account, creds, args.project, args.activate,
                        args.brief)

  def LoginAs(self, account, creds, project, activate, brief):
    """Logs in with valid credentials."""
    if not activate:
      return creds
    properties.PersistProperty(properties.VALUES.core.account, account)
    if project:
      properties.PersistProperty(properties.VALUES.core.project, project)

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
      log.status.write('Saved Application Default Credentials.\n')

    if not brief:
      log.status.write(
          '\nYou are now logged in as [{account}].\n'
          'Your current project is [{project}].  You can change this setting '
          'by running:\n  $ gcloud config set project PROJECT_ID\n'.format(
              account=account, project=properties.VALUES.core.project.Get()))
    return creds

  def DoInstalledAppBrowserFlow(self, launch_browser, scopes):
    """Launches a browser to get credentials."""
    try:
      return c_store.AcquireFromWebFlow(launch_browser=launch_browser,
                                        scopes=scopes)
    except c_store.FlowError:
      msg = 'There was a problem with web authentication.'
      if launch_browser:
        msg += ' Try running again with --no-launch-browser.'
      log.error(msg)
      raise
