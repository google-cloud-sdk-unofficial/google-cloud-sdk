#!/usr/bin/env python
"""Utilities to load Google Auth credentials from gcloud."""

import logging
import subprocess  # pylint: disable=unused-import
from typing import Iterator, List, Optional

from google.oauth2 import credentials as google_oauth2

import bq_auth_flags
import bq_flags
import bq_utils
from gcloud_wrapper import gcloud_runner
from utils import bq_error

ERROR_TEXT_PRODUCED_IF_GCLOUD_NOT_FOUND = "No such file or directory: 'gcloud'"


def LoadCredential() -> google_oauth2.Credentials:
  """Loads credentials by calling gcloud commands."""
  logging.info('Loading auth credentials from gcloud')
  access_token = _GetAccessTokenAndPrintOutput()
  refresh_token = _GetRefreshTokenAndPrintOutput()
  return google_oauth2.Credentials(
      token=access_token,
      refresh_token=refresh_token,
      quota_project_id=bq_utils.GetResolvedQuotaProjectID(
          bq_auth_flags.QUOTA_PROJECT_ID.value, bq_flags.PROJECT_ID.value
      ),
  )


def _GetAccessTokenAndPrintOutput() -> Optional[str]:
  return _GetTokenFromGcloudAndPrintOtherOutput(['auth', 'print-access-token'])


def _GetRefreshTokenAndPrintOutput() -> Optional[str]:
  return _GetTokenFromGcloudAndPrintOtherOutput(['auth', 'print-refresh-token'])


def _GetTokenFromGcloudAndPrintOtherOutput(cmd: List[str]) -> Optional[str]:
  """Returns a token or prints other messages from the given gcloud command."""
  try:
    token = None
    for output in _RunGcloudCommand(cmd):
      if output and ' ' not in output:
        # Token is a non-empty string of non-space characters.
        token = output
        break
      else:
        print(output)
    return token
  except bq_error.BigqueryError as e:
    single_line_error_msg = str(e).replace('\n', '')
    if 'security key' in single_line_error_msg:
      raise bq_error.BigqueryError(
          'Access token has expired. Did you touch the security key within the'
          ' timeout window?\n'
          + _GetReauthMessage()
      )
    elif 'Refresh token has expired' in single_line_error_msg:
      raise bq_error.BigqueryError(
          'Refresh token has expired. ' + _GetReauthMessage()
      )
    elif 'do not support refresh tokens' in single_line_error_msg:
      # It's expected that certain credential types don't support refresh token.
      return None
    else:
      raise bq_error.BigqueryError(
          'Error retrieving auth credentials from gcloud: %s' % str(e)
      )
  except Exception as e:  # pylint: disable=broad-exception-caught
    single_line_error_msg = str(e).replace('\n', '')
    if ERROR_TEXT_PRODUCED_IF_GCLOUD_NOT_FOUND in single_line_error_msg:
      raise bq_error.BigqueryError(
          "'gcloud' not found but is required for authentication. To install,"
          ' follow these instructions:'
          ' https://cloud.google.com/sdk/docs/install'
      )
    raise bq_error.BigqueryError(
        'Error retrieving auth credentials from gcloud: %s' % str(e)
    )


def _RunGcloudCommand(cmd: List[str]) -> Iterator[str]:
  """Runs the given gcloud command, yields the output, and returns the final status code."""
  stderr = subprocess.STDOUT  # pylint:disable=unused-variable
  proc = gcloud_runner.run_gcloud_command(cmd, stderr=stderr)
  error_msgs = []
  if proc.stdout:
    for stdout_line in iter(proc.stdout.readline, ''):
      line = str(stdout_line).strip()
      if line.startswith('ERROR:') or error_msgs:
        error_msgs.append(line)
      else:
        yield line
    proc.stdout.close()
  return_code = proc.wait()
  if return_code:
    raise bq_error.BigqueryError('\n'.join(error_msgs))


def _GetReauthMessage() -> str:
  gcloud_command = '$ gcloud auth login' + (
      ' --enable-gdrive-access' if bq_flags.ENABLE_GDRIVE.value else ''
  )
  return 'To re-authenticate, run:\n\n%s' % gcloud_command
