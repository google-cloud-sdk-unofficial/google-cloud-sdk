# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""A command that prints access tokens."""


import textwrap
import time

from google.auth import exceptions as google_auth_exceptions
from googlecloudsdk.api_lib.auth import exceptions as auth_exceptions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.command_lib.auth import auth_util as auth_command_util
from googlecloudsdk.command_lib.auth import flags as auth_flags
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
_MTLS_WARNING_INTERVAL_SECONDS = 24 * 60 * 60  # Seconds in a day
_MTLS_WARNING_LAST_SHOWN_CONFIG_KEY = 'mtls_warning_last_shown'


class FakeCredentials(object):
  """An access token container.

  oauth2client and google-auth are both supported by gcloud as the auth library.
  credentials in oauth2client store the access token in the "access_token"
  filed. google-auth stores it in the "token" filed. We use this fake
  credentials class to unify them.
  """

  def __init__(self, token):
    self.token = token


def _ShowMTLSWarningOnceDaily():
  """Checks if mTLS warning should be shown and shows it if needed.

  The warning is shown at most once per day.
  """
  current_time = time.time()

  should_show_warning = True
  active_config_store = config.GetConfigStore()

  if active_config_store:
    last_shown_str = active_config_store.Get(
        _MTLS_WARNING_LAST_SHOWN_CONFIG_KEY
    )
    if last_shown_str:
      try:
        last_shown = float(last_shown_str)
        if (current_time - last_shown) < _MTLS_WARNING_INTERVAL_SECONDS:
          should_show_warning = False
      except ValueError:
        # If the stored value is not a valid float,
        # treat it as if the warning has never been shown.
        log.debug(
            'Could not parse float from [%s] for %s.',
            last_shown_str,
            _MTLS_WARNING_LAST_SHOWN_CONFIG_KEY,
        )

  if should_show_warning:
    log.warning(textwrap.dedent("""\
        Warning: This access token is for the gcloud CLI tool itself and is \
bound to its specific client ID, which requires Certificate Based Access (CBA). \
This means it can only be used with CBA-enabled API endpoints.

        If you need a token for your own application code or scripts, you \
should use Application Default Credentials (ADC). Obtain an ADC \
token by running:
          1.  gcloud auth application-default login (if you haven't already)
          2.  gcloud auth application-default print-access-token

        ADC tokens are intended for local development and do not have the \
same CBA restrictions."""))
    # Update the config store with the current timestamp
    if active_config_store:
      active_config_store.Set(
          _MTLS_WARNING_LAST_SHOWN_CONFIG_KEY, str(current_time)
      )


@base.UniverseCompatible
class AccessToken(base.Command):
  """Print an access token for the specified account."""

  detailed_help = {
      'DESCRIPTION': """\
        {description}
        See [RFC6749](https://tools.ietf.org/html/rfc6749) for more
        information about access tokens.

        Note that token itself may not be enough to access some services.
        If you use the token with curl or similar tools, you may see
        permission errors similar to "API has not been used in
        project 32555940559 before or it is disabled.". If it happens, you may
        need to provide a quota project in the "X-Goog-User-Project" header.
        For example,

          $ curl -H "X-Goog-User-Project: your-project" -H "Authorization: Bearer $(gcloud auth print-access-token)" foo.googleapis.com

        The identity that granted the token must have the
        serviceusage.services.use permission on the provided project. See
        https://cloud.google.com/apis/docs/system-parameters for more
        information.
        """,
      'EXAMPLES': """\
        To print access tokens:

          $ {command}
        """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'account',
        nargs='?',
        help=(
            'Account to get the access token for. If not specified, '
            'the current active account will be used.'
        ),
    )
    parser.add_argument(
        '--lifetime',
        type=arg_parsers.Duration(upper_bound='43200s'),
        help=(
            'Access token lifetime. The default access token '
            'lifetime is 3600 seconds, but you can use this flag to reduce '
            'the lifetime or extend it up to 43200 seconds (12 hours). The '
            'org policy constraint '
            '`constraints/iam.allowServiceAccountCredentialLifetimeExtension`'
            ' must be set if you want to extend the lifetime beyond 3600 '
            'seconds. Note that this flag is for service account '
            'impersonation only, so it must be used together with the '
            '`--impersonate-service-account` flag.'
        ),
    )
    auth_flags.AddScopesFlag(parser, hidden=True)
    parser.display_info.AddFormat('value(token)')

  @c_exc.RaiseErrorInsteadOf(
      auth_exceptions.AuthenticationError,
      google_auth_exceptions.GoogleAuthError,
  )
  def Run(self, args):
    """Run the helper command."""
    if (
        properties.VALUES.context_aware.use_client_certificate.GetBool()
        and properties.IsInternalUserCheck()
    ):
      _ShowMTLSWarningOnceDaily()

    if args.lifetime and not args.impersonate_service_account:
      raise c_exc.InvalidArgumentException(
          '--lifetime',
          'Lifetime flag is for service account impersonation only. It must be '
          'used together with the --impersonate-service-account flag.',
      )

    cred = auth_command_util.LoadCredentialsWithScopes(
        account=args.account,
        scopes=args.scopes,
        trusted_scopes=auth_command_util.GetTrustedScopesWithDrive(),
        impersonation_lifetime=args.lifetime,
    )

    token = cred.token
    if not token:
      raise auth_exceptions.InvalidCredentialsError(
          'No access token could be obtained from the current credentials.'
      )
    return FakeCredentials(token)
