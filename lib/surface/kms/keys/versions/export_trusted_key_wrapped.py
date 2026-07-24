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
"""Export a trusted key wrapped CryptoKeyVersion."""

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.core import log


@base.DefaultUniverseOnly
class ExportTrustedKeyWrapped(base.DescribeCommand):
  r"""Export a trusted key wrapped CryptoKeyVersion.

  Exports a trusted key wrapped version.

  ## EXAMPLES

  The following command exports the trusted key wrapped version `1` of the key
  `frodo` wrapped by the key version `1` of `samwise`:

    $ {command} 1 \
        --key=frodo \
        --keyring=fellowship \
        --location=us-east1 \
        --wrapping-key-version=projects/my-project/locations/us-east1/keyRings/fellowship/cryptoKeys/samwise/cryptoKeyVersions/1 \
        --wrapped-key-file=/tmp/my/public_key.file
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyVersionResourceArgument(parser, 'to export')
    flags.AddWrappedKeyFileFlag(parser, 'to store the wrapped key material')
    parser.add_argument(
        '--wrapping-key-version',
        required=True,
        help=(
            'The resource name of the CryptoKeyVersion to use as a wrapping'
            ' key.'
        ),
    )

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    version_ref = flags.ParseCryptoKeyVersionName(args)
    if not version_ref.Name():
      raise exceptions.InvalidArgumentException(
          'version', 'version id must be non-empty.'
      )
    req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsExportTrustedKeyWrappedCryptoKeyVersionRequest(  # pylint: disable=line-too-long
        name=version_ref.RelativeName(),
        wrappingKey=args.wrapping_key_version,
    )
    resp = client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.ExportTrustedKeyWrappedCryptoKeyVersion(
        req
    )

    log.WriteToFileOrStdout(
        args.wrapped_key_file if args.wrapped_key_file else '-',
        resp.wrappedKey,
        overwrite=True,
        binary=True,
        private=True,
    )
