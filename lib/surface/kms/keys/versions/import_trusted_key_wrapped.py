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
"""Import a trusted key wrapped CryptoKeyVersion."""

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.kms import maps
from googlecloudsdk.core.util import files


@base.DefaultUniverseOnly
class ImportTrustedKeyWrapped(base.Command):
  r"""Import a trusted key wrapped CryptoKeyVersion.

  Imports a trusted key wrapped version.

  ## EXAMPLES

  The following command imports a key into version `1` of `frodo`:

    $ {command} \
        --version=1 \
        --key=frodo \
        --keyring=fellowship \
        --location=us-east1 \
        --importing-key-version=projects/my-project/locations/us-east1/keyRings/fellowship/cryptoKeys/samwise/cryptoKeyVersions/1 \
        --algorithm=aes-256-gcm \
        --wrapped-key-file=/tmp/my/wrapped_key.file
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyResourceFlags(parser, 'The containing key to import into.')
    flags.AddCryptoKeyVersionFlag(
        parser, 'to re-import into. Omit this field for first-time import'
    )
    flags.AddWrappedKeyFileFlag(parser, 'to import')
    flags.AddImportedVersionAlgorithmFlag(parser)
    parser.add_argument(
        '--importing-key-version',
        required=True,
        help=(
            'The resource name of the CryptoKeyVersion to use as an '
            'importing key.'
        ),
    )

  def _ReadFile(self, path, max_bytes):
    data = files.ReadBinaryFileContents(path)
    if len(data) > max_bytes:
      raise exceptions.BadFileException(
          'The file is larger than the maximum size of {0} bytes.'.format(
              max_bytes
          )
      )
    return data

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    if not args.wrapped_key_file:
      raise exceptions.RequiredArgumentException(
          '--wrapped-key-file', 'A pre-wrapped key must be provided.'
      )

    try:
      wrapped_key_bytes = self._ReadFile(args.wrapped_key_file, max_bytes=65536)
    except files.Error as e:
      raise exceptions.BadFileException(
          'Failed to read wrapped key file [{0}]: {1}'.format(
              args.wrapped_key_file, e
          )
      )

    req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsImportTrustedKeyWrappedCryptoKeyVersionRequest(  # pylint: disable=line-too-long
        parent=flags.ParseCryptoKeyName(args).RelativeName(),
        importTrustedKeyWrappedCryptoKeyVersionRequest=messages.ImportTrustedKeyWrappedCryptoKeyVersionRequest(
            importingKey=args.importing_key_version,
            wrappedKey=wrapped_key_bytes,
            algorithm=maps.ALGORITHM_MAPPER_FOR_TRUSTED_IMPORT.GetEnumForChoice(
                args.algorithm
            ),
        ),
    )

    if args.version:
      req.importTrustedKeyWrappedCryptoKeyVersionRequest.cryptoKeyVersion = (
          flags.ParseCryptoKeyVersionName(args).RelativeName()
      )

    return client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.ImportTrustedKeyWrappedCryptoKeyVersion(
        req
    )
