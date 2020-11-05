# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command to create a configuration file to allow authentication from 3rd party sources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files

OAUTH_URL = 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource='
RESOURCE_TYPE = 'credential configuration file'


class CredConfigError(Exception):

  def __init__(self, message):
    super(CredConfigError, self).__init__()
    self.message = message


class CreateCredConfig(base.CreateCommand):
  """Create a configuration file for generated credentials.

  This command creates a configuration file to allow access to authenticated
  Cloud Platform actions from a variety of external accounts.
  """

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          To create a file-sourced credential configuration for your project, run:

            $ {command} projects/$PROJECT_NUMBER/locations/$REGION/workloadIdentityPools/$WORKLOAD_POOL_ID/providers/$PROVIDER_ID --service-account=$EMAIL --credential-source-file=$PATH_TO_OIDC_ID_TOKEN --output-file=credentials.json

          To create a url-sourced credential configuration for your project, run:

            $ {command} projects/$PROJECT_NUMBER/locations/$REGION/workloadIdentityPools/$WORKLOAD_POOL_ID/providers/$PROVIDER_ID --service-account=$EMAIL --credential-source-url=$URL_FOR_OIDC_TOKEN --credential-source-headers=Key=Value --output-file=credentials.json

          To create an aws-based credential configuration for your project, run:

            $ {command} projects/$PROJECT_NUMBER/locations/$REGION/workloadIdentityPools/$WORKLOAD_POOL_ID/providers/$PROVIDER_ID --service-account=$EMAIL --aws --output-file=credentials.json

          To create an azure-based credential configuration for your project, run:

            $ {command} projects/$PROJECT_NUMBER/locations/$REGION/workloadIdentityPools/$WORKLOAD_POOL_ID/providers/$PROVIDER_ID --service-account=$EMAIL --azure --app-id-uri=$URI_FOR_AZURE_APP_ID --output-file=credentials.json

          To use the resulting file for any of these commands, set the GOOGLE_APPLICATION_CREDENTIALS environment variable to point to the generated file
          """),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'audience', help='The workload identity pool provider resource name.')
    parser.add_argument(
        '--service-account',
        help='The email of the service account to impersonate.')
    parser.add_argument(
        '--credential-source-file',
        help='Location of the credential source file.')
    parser.add_argument(
        '--credential-source-url',
        help='URL to obtain the credential from.')
    parser.add_argument(
        '--credential-source-headers',
        type=arg_parsers.ArgDict(),
        metavar='key=value',
        help='Headers to use when querying the credential-source-url.')
    parser.add_argument('--aws', help='Use AWS.', action='store_true')
    parser.add_argument('--azure', help='Use Azure.', action='store_true')
    parser.add_argument(
        '--app-id-uri',
        help='The custom Application ID URI for the Azure access token.')
    parser.add_argument(
        '--output-file',
        help='Location to store the generated credential configuration file.',
        required=True)
    parser.add_argument(
        '--subject-token-type',
        help='The type of token being used for authorization.')

  def Run(self, args):
    try:
      source_count = _get_credential_source_count(args)
      if source_count == 0:
        raise CredConfigError('A credential source needs to be specified')
      if source_count > 1:
        raise CredConfigError(
            'Only one single credential source can be specified')

      output = {
          'type': 'external_account',
          'audience': '//iam.googleapis.com/' + args.audience,
          'subject_token_type': _get_token_type(args),
          'token_url': 'https://sts.googleapis.com/v1beta/token',
          'credential_source': _get_credential_source(args),
      }

      if args.service_account:
        output['service_account_impersonation_url'] = ''.join((
            'https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/',
            args.service_account, ':generateAccessToken'))

      files.WriteFileContents(args.output_file, json.dumps(output))
      log.CreatedResource(args.output_file, RESOURCE_TYPE)
    except CredConfigError as cce:
      log.CreatedResource(args.output_file, RESOURCE_TYPE, failed=cce.message)


def _get_token_type(args):
  """Determines the token type based on the credential source used."""
  if args.aws:
    return 'urn:ietf:params:aws:token-type:aws4_request'
  if args.azure:
    return 'urn:ietf:params:oauth:token-type:jwt'
  return args.subject_token_type or 'urn:ietf:params:oauth:token-type:jwt'


def _get_credential_source_count(args):
  """Determines the number of credential sources used."""
  sources = 0
  if args.credential_source_file:
    sources += 1
  if args.credential_source_url:
    sources += 1
  if args.aws:
    sources += 1
  if args.azure:
    sources += 1

  return sources


def _get_credential_source(args):
  """Gets all details of the chosen credential source."""
  if args.credential_source_file:
    return {'file': args.credential_source_file}

  if args.credential_source_url:
    credential_source = {'url': args.credential_source_url}
    if args.credential_source_headers:
      credential_source['headers'] = args.credential_source_headers
    return credential_source

  if args.aws:
    return {
        'environment_id':
            'aws1',
        'region_url':
            'http://169.254.169.254/latest/meta-data/placement/availability-zone',
        'url':
            'http://169.254.169.254/latest/meta-data/iam/security-credentials',
        'regional_cred_verification_url':
            'https://sts.{region}.amazonaws.com?Action=GetCallerIdentity&Version=2011-06-15'
    }

  if args.azure:
    return {
        'url':
            OAUTH_URL + (args.app_id_uri or
                         'https://iam.googleapis.com/' + args.audience),
        'headers': {
            'Metadata': 'True'
        }
    }

  return {}
