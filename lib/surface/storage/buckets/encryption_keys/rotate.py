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
"""Implementation of buckets encryption-keys rotate command."""

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.core import log


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Rotate(base.Command):
  """Rotate a bucket encryption key version to the latest primary version."""

  detailed_help = {
      'DESCRIPTION': (
          """
      Rotate a bucket encryption key version to the latest primary version.
      """
      ),
      'EXAMPLES': (
          """
      To rotate the specified Cloud KMS key version used in a bucket
      (``gs://my-bucket'') to the latest primary key version:

           $ {command} gs://my-bucket \
              --kms-key-version=projects/my-project/locations/us-central1/\
          keyRings/my-key-ring/cryptoKeys/my-key/cryptoKeyVersions/1
      """
      ),
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'url',
        type=str,
        help='The URL of the bucket resource on which to rotate.',
    )
    parser.add_argument(
        '--kms-key-version',
        required=True,
        type=str,
        help=(
            'Resource name of the Cloud KMS key version matching objects to be'
            ' rotated to the primary key version.'
        ),
    )
    flags.add_async_flag(parser)

  def Run(self, args):
    url = storage_url.storage_url_from_string(args.url)
    errors_util.raise_error_if_not_gcs_bucket(args.command_path, url)
    encryption_util.validate_kms_key_version_resource_path(args.kms_key_version)

    client = api_factory.get_api(url.scheme)
    operation = client.rotate_bucket_encryption_key(
        url.bucket_name, args.kms_key_version
    )

    is_async = args.async_ if args.async_ is not None else True
    if is_async:
      log.status.Print(
          f'Rotation operation [{operation.name}] submitted for bucket'
          f' [{args.url}].\n\nTo check operation status, run:\n  $ gcloud'
          f' storage operations describe {operation.name}'
      )
      return operation

    log.status.Print(f'Rotating CMEK key for bucket [{args.url}]...')
    response = client.wait_for_operation(operation)
    log.status.Print(
        f'Successfully rotated encryption key for bucket [{args.url}].'
    )
    return response
