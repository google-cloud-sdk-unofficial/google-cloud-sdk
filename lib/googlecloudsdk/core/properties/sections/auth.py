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
"""Contains the properties for the 'auth' section."""

import functools
import textwrap

from googlecloudsdk.core import config
from googlecloudsdk.core.properties.types import _Section
from googlecloudsdk.core.properties.validators import _BooleanValidator


class _SectionAuth(_Section):
  """Contains the properties for the 'auth' section."""

  DEFAULT_AUTH_HOST = 'https://accounts.google.com/o/oauth2/auth'
  DEFAULT_TOKEN_HOST = 'https://oauth2.googleapis.com/token'
  DEFAULT_MTLS_TOKEN_HOST = 'https://oauth2.mtls.googleapis.com/token'

  def __init__(self):
    super(_SectionAuth, self).__init__('auth')
    self.auth_host = self._Add(
        'auth_host', hidden=True, default=self.DEFAULT_AUTH_HOST
    )
    self.disable_credentials = self._AddBool(
        'disable_credentials',
        default=False,
        help_text=(
            'If True, `gcloud` will not attempt to load any credentials '
            'or authenticate any requests. This is useful when behind a proxy '
            'that adds authentication to requests.'
        ),
    )
    self.token_host = self._Add(
        'token_host',
        default=self.DEFAULT_TOKEN_HOST,
        help_text=(
            'Overrides the token endpoint to provision access tokens. '
            'It can be used with Private Service Connect.'
        ),
    )
    self.mtls_token_host = self._Add(
        'mtls_token_host',
        default=self.DEFAULT_MTLS_TOKEN_HOST,
        help_text=(
            'Overrides the mtls token endpoint to provision access tokens.'
        ),
        hidden=True,
    )
    self.disable_ssl_validation = self._AddBool(
        'disable_ssl_validation', hidden=True
    )
    self.client_id = self._Add(
        'client_id', hidden=True, default=config.CLOUDSDK_CLIENT_ID
    )
    self.client_secret = self._Add(
        'client_secret', hidden=True, default=config.CLOUDSDK_CLIENT_NOTSOSECRET
    )
    self.authority_selector = self._Add('authority_selector', hidden=True)
    self.authorization_token_file = self._Add(
        'authorization_token_file', hidden=True
    )
    self.credential_file_override = self._Add(
        'credential_file_override', hidden=True
    )
    self.access_token_file = self._Add(
        'access_token_file',
        help_text=(
            'A file path to read the access token. Use this property to '
            'authenticate gcloud with an access token. The credentials '
            'of the active account (if it exists) will be ignored. '
            'The file should contain an access token with no other '
            'information.'
        ),
    )
    self.impersonate_service_account = self._Add(
        'impersonate_service_account',
        help_text=textwrap.dedent("""\
        While set, all API requests will be
        made as the given service account or target service account in an
        impersonation delegation chain instead of the currently selected
        account. You can specify either a single service account as the
        impersonator, or a comma-separated list of service accounts to
        create an impersonation delegation chain. This is done without
        needing to create, download, or activate a key for the service
        account or accounts.
        +
        In order to make API requests as a service account, your
        currently selected account must have an IAM role that includes
        the `iam.serviceAccounts.getAccessToken` permission for the
        service account or accounts.
        +
        The `roles/iam.serviceAccountTokenCreator` role has
        the `iam.serviceAccounts.getAccessToken permission`. You can
        also create a custom role.
        +
        You can specify a list of service accounts, separated with
        commas. This creates an impersonation delegation chain in which
        each service account delegates its permissions to the next
        service account in the chain. Each service account in the list
        must have the `roles/iam.serviceAccountTokenCreator` role on the
        next service account in the list. For example, when the property is set
        through `gcloud config set auth/impersonate_service_account=`
        ``SERVICE_ACCOUNT_1'',``SERVICE_ACCOUNT_2'',
        the active account must have the
        `roles/iam.serviceAccountTokenCreator` role on
        ``SERVICE_ACCOUNT_1'', which must have the
        `roles/iam.serviceAccountTokenCreator` role on
        ``SERVICE_ACCOUNT_2''.
        ``SERVICE_ACCOUNT_1'' is the impersonated service
        account and ``SERVICE_ACCOUNT_2'' is the delegate.
        """),
    )
    self.disable_code_verifier = self._AddBool(
        'disable_code_verifier',
        default=False,
        hidden=True,
        help_text=(
            'Disable code verifier in 3LO auth flow. See '
            'https://tools.ietf.org/html/rfc7636 for more information '
            'about code verifier.'
        ),
    )
    self.token_introspection_endpoint = self._Add(
        'token_introspection_endpoint',
        hidden=True,
        help_text=(
            'Overrides the endpoint used for token introspection with '
            'Workload and Workforce Identity Federation. It can be used with '
            'Private Service Connect.'
        ),
    )
    self.login_config_file = self._Add(
        'login_config_file',
        help_text=(
            'Sets the created login configuration file in'
            ' auth/login_config_file. Calling `gcloud auth login` will'
            ' automatically use this login configuration unless it is'
            ' explicitly unset.'
        ),
    )
    self.service_account_use_self_signed_jwt = self._Add(
        'service_account_use_self_signed_jwt',
        default=False,
        help_text=(
            'If True, use self signed jwt flow to get service account'
            ' credentials access token. This only applies to service account'
            ' json file and not to the legacy .p12 file.'
        ),
        validator=functools.partial(
            _BooleanValidator, 'service_account_use_self_signed_jwt'
        ),
        choices=('true', 'false'),
    )
    self.service_account_disable_id_token_refresh = self._AddBool(
        'service_account_disable_id_token_refresh',
        default=False,
        help_text='If True, disable ID token refresh for service account.',
    )
    self.git_helper_use_adc = self._AddBool(
        'git_helper_use_adc',
        default=False,
        hidden=True,
        help_text=(
            'If True, `gcloud auth git-helper` will use Application Default'
            ' Credentials.'
        ),
    )
    self.enable_sts_revoke_workforce_token = self._AddBool(
        'enable_sts_revoke_workforce_token',
        hidden=True,
        default=False,
        help_text='If True, use STS revoke endpoint to revoke workforce token.',
    )
