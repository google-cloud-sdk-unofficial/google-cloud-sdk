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

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.core.console import console_io


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
    base.ASYNC_FLAG.AddToParser(parser)

  # TODO(b/556305006): Call rotate_bucket_encryption_key API.
  def Run(self, args):
    url = storage_url.storage_url_from_string(args.url)
    errors_util.raise_error_if_not_gcs_bucket(args.command_path, url)
    encryption_util.validate_kms_key_version_resource_path(args.kms_key_version)

    console_io.PromptContinue(
        message=(
            f'The KMS key version [{args.kms_key_version}] used in bucket'
            f' [{args.url}] will be rotated to the latest primary key version.'
            f' All objects in {args.url} protected by this specific key'
            ' version will be updated to the new key version.'
        ),
        cancel_on_no=True,
    )
