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
"""Implementation of objects rewrite command for transforming cloud objects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags


@base.Hidden
class Rewrite(base.Command):
  """Rewrite Cloud Storage objects."""

  detailed_help = {
      'DESCRIPTION':
          """
      Rewrite Cloud Storage objects.
      """,
      'EXAMPLES':
          """

      Rewrite a Google Cloud Storage object's with a new encryption key:

        $ {command} gs://bucket/my-object --update-encryption-key

      Change the storage class on all JPG objects in the bucket:

        $ {command} gs://bucket/*.jpg --storage-class nearline
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url', nargs='+', help='Specifies URL of objects to rewrite.')
    parser.add_argument(
        '-I',
        '--stdin',
        action='store_true',
        help='Reads the list of objects to rewrite from stdin. This allows you'
        ' to run a program that generates the list of objects to rewrite.')
    parser.add_argument(
        '-k',
        '--update-encryption-key',
        action='store_true',
        help='Rewrite objects with the current gcloud storage encryption key.'
        ' The value for the encryption key may be either a base64-encoded CSEK'
        ' or a fully qualified KMS key name. If no value is specified for'
        ' the encryption key, gcloud ignores this flag. Instead, rewritten'
        " objects' are encrypted with the bucket's default KMS key, if one is"
        ' set, or Google-managed encryption, if no default KMS key is set.')
    parser.add_argument(
        '-O',
        '--do-not-preserve-acls',
        action='store_true',
        help='When a bucket has uniform bucket-level access (UBLA) enabled,'
        ' this flag is required and will skip all ACL checks. When a bucket has'
        " UBLA disabled, the -O flag rewrites objects with the bucket's default"
        ' object ACL instead of the existing object ACL. This is needed if you'
        ' do not have OWNER permission on the object.')
    parser.add_argument(
        '-R',
        '-r',
        '--recursive',
        action='store_true',
        help='Causes bucket or bucket subdirectory contents to be rewritten'
        ' recursively.')
    parser.add_argument(
        '-s',
        '--storage-class',
        action='store_true',
        help='Rewrites objects using the specified storage class.')
    flags.add_precondition_flags(parser)

  def Run(self, args):
    del args  # Unused.
    raise NotImplementedError
