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
"""Update a key version."""


from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import exceptions as kms_exceptions
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.kms import maps
from googlecloudsdk.core import properties


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  r"""Update a key version.

  {command} can be used to update the key versions. For keys of any protection
  level, you can update the key version's state to enable or disable it.

  For external keys, you can update the protection level to transition between
  the `external` and `external-vpc` protection levels. For key versions with the
  `external` protection level, you can also update the external key URI. For key
  versions with the `external-vpc` protection level, you can also update the
  ekm connection key path or the crypto key backend.

  ## EXAMPLES

  The following command enables the key version 8 of key `frodo`
  within keyring `fellowship` and location `us-east1`:

    $ {command} 8 --location=us-east1 \
                  --keyring=fellowship \
                  --key=frodo \
                  --state=enabled

  The following command disables the key version 8 of key `frodo`
  within keyring `fellowship` and location `us-east1`:

    $ {command} 8 --location=us-east1 \
                  --keyring=fellowship \
                  --key=frodo \
                  --state=disabled

  The following command updates the external key URI of version 8 of key `frodo`
  within keyring `fellowship` and location `us-east1`:

    $ {command} 8 --location=us-east1 \
                  --keyring=fellowship \
                  --key=frodo \
                  --external-key-uri=https://example.kms/v0/some/key/path

  The following command updates the ekm connection key path of version 8 of key
  `bilbo` within keyring `fellowship` and location `us-east1`:

    $ {command} 8 --location=us-east1 \
                  --keyring=fellowship \
                  --key=bilbo \
                  --ekm-connection-key-path=v0/some/key/path

  The following command updates the protection level to `external` and
  the external key URI of version 8 of key `frodo` within keyring
  `fellowship` and location `us-east1`:

    $ {command} 8 --location=us-east1 \
                  --keyring=fellowship \
                  --key=frodo \
                  --protection-level=external \
                  --external-key-uri=https://example.kms/v0/some/key/path

  The following command updates the protection level to `external-vpc`, sets the
  crypto key backend, and sets the ekm connection key path of version 8 of key
  `bilbo` within keyring `fellowship` and location `us-east1`:

    $ {command} 8 --location=us-east1 \
                  --keyring=fellowship \
                  --key=bilbo \
                  --protection-level=external-vpc \
                  --crypto-key-backend="projects/$(gcloud config get project)/locations/us-east1/ekmConnections/eagles" \
                  --ekm-connection-key-path=v0/some/key/path
  """

  @classmethod
  def Args(cls, parser):
    flags.AddKeyVersionResourceArgument(parser, 'to describe')
    flags.AddExternalKeyUriFlag(parser)
    flags.AddCryptoKeyVersionEkmConnectionKeyPathFlag(parser)
    flags.AddStateFlag(parser)
    if properties.IsDefaultUniverse() and cls.ReleaseTrack() in [
        base.ReleaseTrack.ALPHA,
        base.ReleaseTrack.BETA,
    ]:
      flags.AddCryptoKeyVersionProtectionLevelFlag(parser)
      flags.AddCryptoKeyVersionBackendFlag(parser)

  def ProcessFlags(self, args):
    fields_to_update = []

    if args.external_key_uri:
      fields_to_update.append('externalProtectionLevelOptions.externalKeyUri')
    if args.ekm_connection_key_path:
      fields_to_update.append(
          'externalProtectionLevelOptions.ekmConnectionKeyPath')
    if args.state:
      fields_to_update.append('state')
    if getattr(args, 'protection_level', None):
      fields_to_update.append('protectionLevel')
    if getattr(args, 'crypto_key_backend', None):
      fields_to_update.append(
          'externalProtectionLevelOptions.ekmConnectionBackendOverride'
      )

    # Raise an exception when no update field is specified.
    if not fields_to_update:
      raise kms_exceptions.UpdateError(
          'An error occurred: --external-key-uri or --ekm-connection-key-path'
          ' or --state or --protection-level or --crypto-key-backend must be'
          ' specified.'
      )

    return fields_to_update

  def CreateRequest(self, args, messages, fields_to_update):
    # pylint: disable=line-too-long
    version_ref = flags.ParseCryptoKeyVersionName(args)

    protection_level = None
    if getattr(args, 'protection_level', None):
      protection_level = (
          messages.CryptoKeyVersion.ProtectionLevelValueValuesEnum.lookup_by_name(
              args.protection_level.upper().replace('-', '_')
          )
      )

    req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsPatchRequest(
        name=version_ref.RelativeName(),
        cryptoKeyVersion=messages.CryptoKeyVersion(
            state=maps.CRYPTO_KEY_VERSION_STATE_MAPPER.GetEnumForChoice(
                args.state
            ),
            protectionLevel=protection_level,
            externalProtectionLevelOptions=messages.ExternalProtectionLevelOptions(
                externalKeyUri=args.external_key_uri,
                ekmConnectionKeyPath=args.ekm_connection_key_path,
                ekmConnectionBackendOverride=getattr(
                    args, 'crypto_key_backend', None
                ),
            ),
        ),
    )

    req.updateMask = ','.join(fields_to_update)

    return req

  def CheckKeyIsExternal(self, key_version, messages, protection_level):
    if (
        key_version.protectionLevel
        != messages.CryptoKeyVersion.ProtectionLevelValueValuesEnum.EXTERNAL
        and protection_level != 'external'
    ):
      raise kms_exceptions.UpdateError(
          'External key URI updates are only available for key versions '
          'with EXTERNAL protection level'
      )

  def CheckKeyIsExternalVpc(self, key_version, messages, protection_level):
    if (
        key_version.protectionLevel
        != messages.CryptoKeyVersion.ProtectionLevelValueValuesEnum.EXTERNAL_VPC
        and protection_level != 'external-vpc'
    ):
      raise kms_exceptions.UpdateError(
          'EkmConnection key path updates are only available for key versions '
          'with EXTERNAL_VPC protection level'
      )

  def Run(self, args):
    # pylint: disable=line-too-long
    fields_to_update = self.ProcessFlags(args)

    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    version_ref = flags.ParseCryptoKeyVersionName(args)

    # Try to get the cryptoKeyVersion and raise an exception if it doesn't exist.
    key_version = client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.Get(
        messages
        .CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetRequest(
            name=version_ref.RelativeName()))

    protection_level = getattr(args, 'protection_level', None)
    crypto_key_backend = getattr(args, 'crypto_key_backend', None)

    # Check that this key version's ProtectionLevel is EXTERNAL
    if args.external_key_uri:
      self.CheckKeyIsExternal(key_version, messages, protection_level)

    if args.ekm_connection_key_path or crypto_key_backend:
      self.CheckKeyIsExternalVpc(key_version, messages, protection_level)

    # Make update request
    update_req = self.CreateRequest(args, messages, fields_to_update)
    return client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.Patch(
        update_req)
