#!/usr/bin/env python
"""Utilities to create Google Auth credentials."""

import logging
import subprocess
from typing import Optional, Tuple, Union

from absl import app
from google.auth.compute_engine import credentials as compute_engine
from google.oauth2 import credentials as google_oauth2
from google.oauth2 import service_account

import bq_auth_flags
import bq_flags
import bq_utils
from utils import bq_error


GoogleAuthCredentialsUnionType = Union[
    google_oauth2.Credentials,
    service_account.Credentials,
    compute_engine.Credentials,
]


def GetCredentialsFromFlags() -> GoogleAuthCredentialsUnionType:
  """Returns credentials based on BQ CLI auth flags.

  Returns: An OAuth2, compute engine, or service account credentials objects
  based on BQ CLI auth flag values.

  Raises:
  app.UsageError, invalid flag values.
  bq_error.BigqueryError, error getting credentials.
  """
  if bq_auth_flags.APPLICATION_DEFAULT_CREDENTIAL_FILE.value:
    raise app.UsageError(
        'The --application_default_credential_file flag is being deprecated.'
        ' For now, this flag can still be used by forcing the legacy'
        ' authentication library with --nouse_google_auth.'
    )
  if (
      bq_auth_flags.SERVICE_ACCOUNT_PRIVATE_KEY_PASSWORD.default
      != bq_auth_flags.SERVICE_ACCOUNT_PRIVATE_KEY_PASSWORD.value
  ):
    raise app.UsageError(bq_error.P12_DEPRECATION_MESSAGE)

  if bq_auth_flags.OAUTH_ACCESS_TOKEN.value:
    logging.info('Loading auth credentials from --oauth_access_token')
    return google_oauth2.Credentials(
        token=bq_auth_flags.OAUTH_ACCESS_TOKEN.value,
        quota_project_id=bq_utils.GetResolvedQuotaProjectID(
            bq_auth_flags.QUOTA_PROJECT_ID.value, bq_flags.PROJECT_ID.value
        ),
    )
  else:
    logging.info('No `oauth_access_token`, load credentials elsewhere')

  if bq_auth_flags.USE_GCE_SERVICE_ACCOUNT.value:
    logging.info('Loading auth credentials with --use_gce_service_account')
    return compute_engine.Credentials(
        quota_project_id=bq_utils.GetResolvedQuotaProjectID(
            bq_auth_flags.QUOTA_PROJECT_ID.value, fallback_project_id=None
        ),
    )
  else:
    logging.info('No `use_gce_service_account`, load credentials elsewhere')


  # Use gcloud to get currently active credentials.
  logging.info('Loading auth credentials from gcloud')
  (access_token, refresh_token) = _RunGcloudForOAuthTokens()
  return google_oauth2.Credentials(
      token=access_token,
      refresh_token=refresh_token,
      quota_project_id=bq_utils.GetResolvedQuotaProjectID(
          bq_auth_flags.QUOTA_PROJECT_ID.value, bq_flags.PROJECT_ID.value
      ),
  )




def _RunGcloudForOAuthTokens() -> Tuple[Optional[str], Optional[str]]:
  """Returns an (access token, refresh token) tuple by calling gcloud auth commands."""
  access_token = None
  try:
    access_token_result = subprocess.run(
        ['gcloud', 'auth', 'print-access-token'],
        check=True,
        capture_output=True,
    )
    access_token = access_token_result.stdout.decode('utf-8').strip()
    refresh_token_result = subprocess.run(
        ['gcloud', 'auth', 'print-refresh-token'],
        check=True,
        capture_output=True,
    )
    refresh_token = refresh_token_result.stdout.decode('utf-8').strip()
    return (access_token, refresh_token)
  except subprocess.CalledProcessError as e:
    if 'Refresh token has expired' in str(e.stderr):
      raise bq_error.BigqueryError(
          'Refresh token has expired. ' + _GetReauthMessage()
      )
    elif 'do not support refresh tokens' in str(e.stderr):
      return (access_token, None)
    else:
      raise bq_error.BigqueryError(
          'Error retrieving auth credentials from gcloud.\n'
          'Stdout:\n%s\nStderr:\n%s' % (str(e.stdout), str(e.stderr))
      )
  except Exception as e:  # pylint: disable=broad-exception-caught
    if "No such file or directory: 'gcloud'" in str(e):
      raise bq_error.BigqueryError(
          "'gcloud' not found but is required for authentication. To install,"
          ' follow these instructions:'
          ' https://cloud.google.com/sdk/docs/install'
      )
    raise bq_error.BigqueryError(
        'Error retrieving auth credentials from gcloud: %s' % str(e)
    )


def _GetReauthMessage() -> str:
  gcloud_command = '$ gcloud auth login' + (
      ' --enable-gdrive-access' if bq_flags.ENABLE_GDRIVE.value else ''
  )
  return 'To re-authenticate, run:\n\n%s' % gcloud_command
