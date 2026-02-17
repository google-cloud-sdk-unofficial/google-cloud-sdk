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
"""Command to print an identity token for a specified audience in Google Distributed Cloud zone."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from google.auth import exceptions as google_auth_exceptions
from google.oauth2 import gdch_credentials
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.anthos import binary_operations
from googlecloudsdk.core import log
from googlecloudsdk.core import requests


# TODO(b/464848930): Add standard unit test for the Auth Wrapper library.
class GDCAuthWrapper(binary_operations.StreamingBinaryBackedOperation):
  """Binary operation wrapper for the commands.

  This wrapper is used for the gdc-print-identity-token command which is used
  to print an identity token for a specified audience in Google Distributed
  Cloud zone.

  Typical usage example:

    command_executor = GDCAuthWrapper()
    response = command_executor(
        login_cert,
        login_uri,
        audience,
    )
  """

  def __init__(self, **kwargs):
    super(GDCAuthWrapper, self).__init__(binary='kubectl-anthos', **kwargs)

  def _ParseArgsForCommand(self, login_cert, login_uri, audience, **kwargs):
    del kwargs  # Not Used Here
    exec_args = ['gdc-print-identity-token']
    if login_cert:
      exec_args.extend(['--login-cert', login_cert])
    if login_uri:
      exec_args.extend(['--login-uri', login_uri])
    if audience:
      exec_args.extend(['--audience', audience])
    return exec_args


def AddIDPLoginArg(group):
  """Adds the IDP login arguments to the group.

  Args:
    group: The group to add the IDP login arguments to.
  """

  idp_login_group = group.add_argument_group(
      help='IDP Login Arguments.')
  idp_login_group.add_argument(
      '--login-uri',
      type=str,
      metavar='LOGIN_URI',
      help='Google Distributed Cloud zone IDP login URI.',
      required=True,
  )
  idp_login_group.add_argument(
      '--login-cert',
      type=str,
      metavar='LOGIN_CERT',
      help='Google Distributed Cloud zone CA certificate path',
  )


def AddAudienceArg(group):
  """Adds the Audience argument to the group.

  Args:
    group: The group to add the Audience argument to.
  """

  group.add_argument(
      '--audience',
      type=str,
      metavar='AUDIENCE',
      required=True,
      help=(
          'Intended recipient of the token. '
          'Currently, only one audience can be specified.'
      ),
  )


def AddCredFileArg(group):
  """Adds the Cred file argument to the group.

  Args:
    group: The group to add the Cred file argument to.
  """

  cred_file_group = group.add_argument_group(
      help='Credential File Arguments.')
  cred_file_group.add_argument(
      '--cred-file',
      type=str,
      metavar='CRED_FILE',
      help='Credential file.',
      required=True,
  )


def AddTokenGenerationArgs(group):
  """Adds the Token Generation argument to the group.

  Args:
    group: The group to add the Token Generation argument to.
  """

  token_generation_group = group.add_argument_group(
      required=True,
      mutex=True,
      help='Token Generation Arguments.')
  AddCredFileArg(token_generation_group)
  AddIDPLoginArg(token_generation_group)


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AccessToken(base.DescribeCommand):
  """Print an identity token for a specified audience.

  The methods in the class generates an identity token for a specified
  audience in Google Distributed Cloud zone. The identity token can be generated
  based on IDP login or Service Account Keys.
  """

  @staticmethod
  def Args(parser):
    AddTokenGenerationArgs(parser)
    AddAudienceArg(parser)
    parser.display_info.AddFormat('value(token)')

  def Run(self, args):
    """Runs the command.

    Args:
      args: The arguments passed to the command.

    Returns:
      The identity token.
    """
    if args.cred_file:
      credential = (
          gdch_credentials.ServiceAccountCredentials.from_service_account_file(
              args.cred_file
          )
      )
      credential = credential.with_gdch_audience(args.audience)

      try:
        credential.refresh(requests.GoogleAuthRequest())
      except google_auth_exceptions.RefreshError as e:
        log.error('Failed to refresh credentials: %s', e)
        return None
      return credential
    else:
      command_executor = GDCAuthWrapper()
      response = command_executor(
          login_cert=args.login_cert,
          login_uri=args.login_uri,
          audience=args.audience,
      )

      if response.stderr:
        return response.stderr

      if response.failed:
        return response.failed

      return response.stdout
