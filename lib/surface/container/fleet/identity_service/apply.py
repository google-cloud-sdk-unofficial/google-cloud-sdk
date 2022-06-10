# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""The command to update Identity Service Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys
from googlecloudsdk.command_lib.anthos.common import file_parsers
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
import urllib3

# Pull out the example text so the example command can be one line without the
# py linter complaining. The docgen tool properly breaks it into multiple lines.
EXAMPLES = """\
    To apply an Identity Service configuration for a membership, run:

    $ {command} --membership=MEMBERSHIP_NAME --config=/path/to/identity-service.yaml
"""
# The max number of auth methods allowed per config.
MAX_AUTH_PROVIDERS = 20


class Apply(base.UpdateCommand):
  """Update an Identity Service Feature Spec.

  Applies the authentication configuration to the Identity Service feature spec
  for this membership. This configuration is now the "source of truth" for the
  cluster and can only be updated by using this command or the Cloud Console.
  Any local authentication configuration on the cluster is overwritten by this
  configuration, including any local updates made after you run this command.
  """

  detailed_help = {'EXAMPLES': EXAMPLES}

  feature_name = 'identityservice'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--membership',
        type=str,
        help='The Membership name provided during registration.',
    )
    parser.add_argument(
        '--config',
        type=str,
        help='The path to the identity-service.yaml config file.',
        required=True)

  def Run(self, args):
    # Get fleet memberships (cluster registered with fleet) from GCP Project.
    memberships = base.ListMemberships()
    if not memberships:
      raise exceptions.Error('No Memberships available in the fleet.')

    # Acquire membership.
    membership = None
    # Prompt user for an existing fleet membership if none is provided.
    if not args.membership:
      index = 0
      if len(memberships) > 1:
        index = console_io.PromptChoice(
            options=memberships,
            message='Please specify a membership to apply {}:\n'.format(
                args.config))
      membership = memberships[index]
      sys.stderr.write('Selecting membership [{}].\n'.format(membership))
    else:
      membership = args.membership
      if membership not in memberships:
        raise exceptions.Error(
            'Membership {} is not in the fleet.'.format(membership))

    # Load config YAML file.
    loaded_config = file_parsers.YamlConfigFile(
        file_path=args.config, item_type=file_parsers.LoginConfigObject)

    # Create new identity service feature spec.
    member_config = _parse_config(loaded_config, self.messages)

    # UpdateFeature uses the patch method to update member_configs map, hence
    # there's no need to get the existing feature spec.
    full_name = self.MembershipResourceName(membership)
    specs = {
        full_name:
            self.messages.MembershipFeatureSpec(identityservice=member_config)
    }
    feature = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs(specs))

    # Execute update to apply new identity service feature spec to membership.
    self.Update(['membership_specs'], feature)


def _parse_config(loaded_config, msg):
  """Load FeatureSpec MemberConfig from the parsed ClientConfig CRD yaml file.

  Args:
    loaded_config: YamlConfigFile, The data loaded from the ClientConfig CRD
      yaml file given by the user. YamlConfigFile is from
      googlecloudsdk.command_lib.anthos.common.file_parsers.
    msg: The gkehub messages package.

  Returns:
    member_config: The MemberConfig configuration containing the AuthMethods for
      the IdentityServiceFeatureSpec.
  """

  # Get list of of auth providers from ClientConfig.
  if len(loaded_config.data) != 1:
    raise exceptions.Error('Input config file must contains one YAML document.')
  clientconfig = loaded_config.data[0]
  _validate_clientconfig_meta(clientconfig)
  auth_providers = clientconfig.GetAuthProviders(name_only=False)

  # Don't accept configs containing more auth providers than MAX_AUTH_PROVIDERS
  auth_providers_count = len(auth_providers)
  if auth_providers_count > MAX_AUTH_PROVIDERS:
    err_msg = ('The provided configuration contains {} identity providers. '
               'The maximum number that can be provided is {}.').format(
                   auth_providers_count, MAX_AUTH_PROVIDERS)
    raise exceptions.Error(err_msg)

  # Create empy MemberConfig and populate it with Auth_Provider configurations.
  member_config = msg.IdentityServiceMembershipSpec()
  # The config must contain an OIDC auth_method.
  oidc = False
  for auth_provider in auth_providers:
    # Provision OIDC proto from OIDC ClientConfig dictionary.
    if 'oidc' in auth_provider:
      auth_method = _provision_oidc_config(auth_provider, msg)
      member_config.authMethods.append(auth_method)
      oidc = True
    # LDAP is currently not supported.
    elif 'ldap' in auth_provider:
      log.status.Print('LDAP configuration not supported. Skipping to next.')
  if not oidc:
    raise exceptions.Error('No OIDC config is found.')
  return member_config


def _validate_clientconfig_meta(clientconfig):
  """Validate the basics of the parsed clientconfig yaml for AIS Hub Feature Spec.

  Args:
    clientconfig: The data field of the YamlConfigFile.
  """
  if not isinstance(clientconfig, file_parsers.YamlConfigObject):
    raise exceptions.Error('Invalid ClientConfig template.')
  if ('apiVersion' not in clientconfig or
      clientconfig['apiVersion'] != 'authentication.gke.io/v2alpha1'):
    raise exceptions.Error(
        'Only support "apiVersion: authentication.gke.io/v2alpha1"')
  if ('kind' not in clientconfig or clientconfig['kind'] != 'ClientConfig'):
    raise exceptions.Error('Only support "kind: ClientConfig"')
  if 'spec' not in clientconfig:
    raise exceptions.Error('Missing required field .spec')


def _provision_oidc_config(auth_method, msg):
  """Provision FeatureSpec OIDCConfig from the parsed oidc ClientConfig CRD yaml file.

  Args:
    auth_method: YamlConfigFile, The data loaded from the ClientConfig CRD yaml
      file given by the user. YamlConfigFile is from
      googlecloudsdk.command_lib.anthos.common.file_parsers.
    msg: The gkehub messages package.

  Returns:
    member_config: The MemberConfig configuration containing the AuthMethods for
      the IdentityServiceFeatureSpec.
  """
  auth_method_proto = msg.IdentityServiceAuthMethod()
  auth_method_proto.name = auth_method['name']
  oidc_config = auth_method['oidc']

  # Required Fields.
  if 'issuerURI' not in oidc_config or 'clientID' not in oidc_config:
    raise exceptions.Error(
        'input config file OIDC Config must contain issuerURI and clientID.')
  auth_method_proto.oidcConfig = msg.IdentityServiceOidcConfig()
  auth_method_proto.oidcConfig.issuerUri = oidc_config['issuerURI']
  auth_method_proto.oidcConfig.clientId = oidc_config['clientID']

  _validate_issuer_uri(auth_method_proto.oidcConfig.issuerUri,
                       auth_method['name'])

  # Optional Auth Method Fields.
  if 'proxy' in auth_method:
    auth_method_proto.proxy = auth_method['proxy']

  # Optional OIDC Config Fields.
  if 'certificateAuthorityData' in oidc_config:
    auth_method_proto.oidcConfig.certificateAuthorityData = oidc_config[
        'certificateAuthorityData']
  if 'deployCloudConsoleProxy' in oidc_config:
    auth_method_proto.oidcConfig.deployCloudConsoleProxy = oidc_config[
        'deployCloudConsoleProxy']
  if 'extraParams' in oidc_config:
    auth_method_proto.oidcConfig.extraParams = oidc_config['extraParams']
  if 'groupPrefix' in oidc_config:
    auth_method_proto.oidcConfig.groupPrefix = oidc_config['groupPrefix']
  if 'groupsClaim' in oidc_config:
    auth_method_proto.oidcConfig.groupsClaim = oidc_config['groupsClaim']

  # If groupClaim is empty, then groupPrefix should be empty
  if not auth_method_proto.oidcConfig.groupsClaim and auth_method_proto.oidcConfig.groupPrefix:
    raise exceptions.Error(
        'groupPrefix should be empty for method [{}] because groupsClaim is empty.'
        .format(auth_method['name']))

  if 'kubectlRedirectURI' in oidc_config:
    auth_method_proto.oidcConfig.kubectlRedirectUri = oidc_config[
        'kubectlRedirectURI']
  if 'scopes' in oidc_config:
    auth_method_proto.oidcConfig.scopes = oidc_config['scopes']
  if 'userClaim' in oidc_config:
    auth_method_proto.oidcConfig.userClaim = oidc_config['userClaim']
  if 'userPrefix' in oidc_config:
    auth_method_proto.oidcConfig.userPrefix = oidc_config['userPrefix']
  if 'clientSecret' in oidc_config:
    auth_method_proto.oidcConfig.clientSecret = oidc_config['clientSecret']

  return auth_method_proto


def _validate_issuer_uri(issuer_uri, auth_method_name):
  """Validates Issuer URI field of OIDC config.

  Args:
    issuer_uri: issuer uri to be validated
    auth_method_name: auth method name that has this field
  """
  url = urllib3.util.parse_url(issuer_uri)
  if url.scheme != 'https':
    raise exceptions.Error(
        'issuerURI is invalid for method [{}]. Scheme is not https.'.format(
            auth_method_name))
  if url.path is not None and '.well-known/openid-configuration' in url.path:
    raise exceptions.Error(
        'issuerURI is invalid for method [{}]. issuerURI should not contain [{}].'
        .format(auth_method_name, '.well-known/openid-configuration'))
