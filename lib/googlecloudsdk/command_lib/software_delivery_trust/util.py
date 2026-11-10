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
"""Utilities and helpers for Software Delivery Trust commands."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

API_NAME = 'softwaredeliverytrust'
API_VERSION = 'v1alpha'
KMS_API_NAME = 'cloudkms'
KMS_API_VERSION = 'v1'


def GetClient():
  """Returns the Software Delivery Trust API client."""
  return apis.GetClientInstance(API_NAME, API_VERSION)


def GetMessages():
  """Returns the Software Delivery Trust API messages module."""
  return apis.GetMessagesModule(API_NAME, API_VERSION)


def AddLocationResourceArg(parser, group_help_text, required=True):
  """Adds a resource argument for a Google Cloud location."""
  resource_spec = concepts.ResourceSpec(
      'softwaredeliverytrust.projects.locations',
      resource_name='location',
      locationsId=concepts.ResourceParameterAttributeConfig(
          name='location',
          help_text='Google Cloud location for the {resource}.',
      ),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )
  concept_parser = concept_parsers.ConceptParser.ForResource(
      '--location', resource_spec, group_help_text, required=required
  )
  concept_parser.AddToParser(parser)


def NormalizeGateName(gate):
  """Normalizes a gate name string by stripping optional 'gate=' prefix."""
  if not gate:
    return ''
  gate_str = str(gate).strip()
  if gate_str.startswith('gate='):
    gate_str = gate_str[len('gate=') :].strip()
  return gate_str


def LoadAttestorsFromFile(file_path, messages):
  """Loads attestors configuration from a YAML or JSON file.

  Args:
    file_path: str, path to the YAML or JSON file.
    messages: module, Software Delivery Trust messages module.

  Returns:
    list of messages.Attestor objects.

  Raises:
    exceptions.InvalidArgumentException: if the file format or contents are
    invalid.
  """
  try:
    data = yaml.load_path(file_path)
  except Exception as e:
    raise exceptions.InvalidArgumentException(
        '--attestors-file',
        'Failed to read or parse attestors file [{}]: {}'.format(file_path, e),
    )

  if isinstance(data, dict) and 'attestors' in data:
    items = data['attestors']
  elif isinstance(data, list):
    items = data
  else:
    raise exceptions.InvalidArgumentException(
        '--attestors-file',
        'Invalid attestors file structure in [{}]. Expected a list of'
        ' attestors or a dictionary with an "attestors" key.'.format(file_path),
    )

  if not isinstance(items, list):
    raise exceptions.InvalidArgumentException(
        '--attestors-file',
        'Expected "attestors" to be a list in [{}].'.format(file_path),
    )

  attestors = []
  for i, item in enumerate(items):
    if not isinstance(item, dict):
      raise exceptions.InvalidArgumentException(
          '--attestors-file',
          'Attestor item #{} in [{}] must be a key-value mapping.'.format(
              i + 1, file_path
          ),
      )

    gate = NormalizeGateName(item.get('gate'))
    if not gate:
      raise exceptions.InvalidArgumentException(
          '--attestors-file',
          'Attestor item #{} in [{}] is missing required "gate" field.'.format(
              i + 1, file_path
          ),
      )

    key_ver = (
        item.get('signing-crypto-key-version')
        or item.get('signing_crypto_key_version')
        or item.get('signingCryptoKeyVersion')
    )
    if not key_ver:
      raise exceptions.InvalidArgumentException(
          '--attestors-file',
          'Attestor item #{} (gate "{}") in [{}] is missing required'
          ' "signing-crypto-key-version" field.'.format(i + 1, gate, file_path),
      )

    attestors.append(
        messages.Attestor(
            gate=gate,
            signingCryptoKeyVersion=str(key_ver).strip(),
        )
    )

  return attestors


class SettingsOperationPoller(waiter.CloudOperationPollerNoResources):
  """Poller for Settings update operations that fetches the updated Settings."""

  def __init__(self, client, messages, settings_name):
    super(SettingsOperationPoller, self).__init__(
        client.projects_locations_operations
    )
    self._client = client
    self._messages = messages
    self._settings_name = settings_name

  def GetResult(self, operation):
    get_req = (
        self._messages.SoftwaredeliverytrustProjectsLocationsGetSettingsRequest(
            name=self._settings_name
        )
    )
    settings = self._client.projects_locations.GetSettings(get_req)
    return (
        settings.binaryAuthorizationConfig
        or self._messages.BinaryAuthorizationConfig()
    )


def GetKmsClient():
  """Returns the Cloud KMS API client and messages module."""
  client = apis.GetClientInstance(KMS_API_NAME, KMS_API_VERSION)
  messages = apis.GetMessagesModule(KMS_API_NAME, KMS_API_VERSION)
  return client, messages


def FetchKmsPublicKey(kms_key_version_name):
  """Fetches public key PEM and algorithm for a Cloud KMS CryptoKeyVersion."""
  client, messages = GetKmsClient()
  req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetPublicKeyRequest(
      name=kms_key_version_name
  )
  return client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.GetPublicKey(
      req
  )


def MapKmsAlgorithmToSdTrust(kms_algorithm_name, sdtrust_messages):
  """Maps a Cloud KMS algorithm name string to the SD Trust SignatureAlgorithm enum."""
  enum_cls = sdtrust_messages.PkixPublicKey.SignatureAlgorithmValueValuesEnum
  alg_map = {
      'EC_SIGN_P256_SHA256': enum_cls.EC_SIGN_P256_SHA256,
      'EC_SIGN_P384_SHA384': enum_cls.EC_SIGN_P384_SHA384,
      'EC_SIGN_P521_SHA512': enum_cls.EC_SIGN_P521_SHA512,
      'RSA_SIGN_PSS_2048_SHA256': enum_cls.RSA_SIGN_PSS_2048_SHA256,
      'RSA_SIGN_PSS_3072_SHA256': enum_cls.RSA_SIGN_PSS_3072_SHA256,
      'RSA_SIGN_PSS_4096_SHA256': enum_cls.RSA_SIGN_PSS_4096_SHA256,
      'RSA_SIGN_PSS_4096_SHA512': enum_cls.RSA_SIGN_PSS_4096_SHA512,
      'RSA_SIGN_PKCS1_2048_SHA256': enum_cls.RSA_SIGN_PKCS1_2048_SHA256,
      'RSA_SIGN_PKCS1_3072_SHA256': enum_cls.RSA_SIGN_PKCS1_3072_SHA256,
      'RSA_SIGN_PKCS1_4096_SHA256': enum_cls.RSA_SIGN_PKCS1_4096_SHA256,
      'RSA_SIGN_PKCS1_4096_SHA512': enum_cls.RSA_SIGN_PKCS1_4096_SHA512,
  }
  key = str(kms_algorithm_name)
  if key in alg_map:
    return alg_map[key]
  raise exceptions.InvalidArgumentException(
      '--kms-key-version',
      'Unsupported KMS signature algorithm: {}'.format(kms_algorithm_name),
  )


def MapCliAlgorithmToSdTrust(cli_algorithm_choice, sdtrust_messages):
  """Maps CLI kebab-case choice to the SD Trust SignatureAlgorithm enum."""
  enum_cls = sdtrust_messages.PkixPublicKey.SignatureAlgorithmValueValuesEnum
  cli_map = {
      'ec-sign-p256-sha256': enum_cls.EC_SIGN_P256_SHA256,
      'ec-sign-p384-sha384': enum_cls.EC_SIGN_P384_SHA384,
      'ec-sign-p521-sha512': enum_cls.EC_SIGN_P521_SHA512,
      'rsa-sign-pss-2048-sha256': enum_cls.RSA_SIGN_PSS_2048_SHA256,
      'rsa-sign-pss-3072-sha256': enum_cls.RSA_SIGN_PSS_3072_SHA256,
      'rsa-sign-pss-4096-sha256': enum_cls.RSA_SIGN_PSS_4096_SHA256,
      'rsa-sign-pss-4096-sha512': enum_cls.RSA_SIGN_PSS_4096_SHA512,
      'rsa-sign-pkcs1-2048-sha256': enum_cls.RSA_SIGN_PKCS1_2048_SHA256,
      'rsa-sign-pkcs1-3072-sha256': enum_cls.RSA_SIGN_PKCS1_3072_SHA256,
      'rsa-sign-pkcs1-4096-sha256': enum_cls.RSA_SIGN_PKCS1_4096_SHA256,
      'rsa-sign-pkcs1-4096-sha512': enum_cls.RSA_SIGN_PKCS1_4096_SHA512,
  }
  if cli_algorithm_choice in cli_map:
    return cli_map[cli_algorithm_choice]
  raise exceptions.InvalidArgumentException(
      '--signature-algorithm',
      'Unknown signature algorithm choice: {}'.format(cli_algorithm_choice),
  )


def BuildPublicKeyFromArgs(args, sdtrust_messages):
  """Constructs a PublicKey proto message from parsed CLI arguments."""
  if getattr(args, 'kms_key_version', None):
    kms_pubkey = FetchKmsPublicKey(args.kms_key_version)
    sig_alg = MapKmsAlgorithmToSdTrust(kms_pubkey.algorithm, sdtrust_messages)
    # Default key_id to the KMS key version resource name if not overridden
    key_id = getattr(args, 'key_id', None) or args.kms_key_version
    return sdtrust_messages.PublicKey(
        keyId=key_id,
        pkixPublicKey=sdtrust_messages.PkixPublicKey(
            pem=kms_pubkey.pem,
            signatureAlgorithm=sig_alg,
        ),
    )

  if getattr(args, 'pkix_public_key_file', None):
    if not getattr(args, 'signature_algorithm', None):
      raise exceptions.RequiredArgumentException(
          '--signature-algorithm',
          '--signature-algorithm is required when --pkix-public-key-file is'
          ' specified.',
      )
    pem_content = files.ReadFileContents(args.pkix_public_key_file)
    sig_alg = MapCliAlgorithmToSdTrust(
        args.signature_algorithm, sdtrust_messages
    )
    key_id = getattr(args, 'key_id', None)
    return sdtrust_messages.PublicKey(
        keyId=key_id,
        pkixPublicKey=sdtrust_messages.PkixPublicKey(
            pem=pem_content,
            signatureAlgorithm=sig_alg,
        ),
    )

  return None
