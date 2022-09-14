# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Implementation of hash command for getting formatted file hashes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Hash(base.Command):
  """Calculates hashes on local or cloud files."""

  detailed_help = {
      'DESCRIPTION':
          """
      Calculates hashes on local or cloud files that can be used to compare with
      "gcloud storage ls -L" output. If a specific hash option is not provided,
      this command calculates all gcloud storage-supported hashes for the file.

      Note that gcloud storage automatically performs hash validation when
      uploading or downloading files, so this command is only needed if you want
      to write a script that separately checks the hash for some reason.

      If you calculate a CRC32C hash for the file without a precompiled
      google-crc32c installation, hashing will be very slow.
      """,
      'EXAMPLES':
          """

      To get the MD5 hash of a cloud object:

        $ {command} gs://bucket/object --md5

      To get the CRC32C hash of a local object in hexadecimal:

        $ {command} /dir/object.txt --crc32c --hex
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url', nargs='+', help='Local or cloud URLs of objects to hash.')
    parser.add_argument(
        '-c',
        '--crc32c',
        action='store_true',
        help='Calculate a CRC32c hash for the file.')
    parser.add_argument(
        '--hex',
        action='store_true',
        help='Output hashes in hex format. By default, gsutil uses base64.')
    parser.add_argument(
        '-m',
        '--md5',
        action='store_true',
        help='Calculate a MD5 hash for the file.')

  def Run(self, args):
    del args  # Unused.
    raise NotImplementedError
