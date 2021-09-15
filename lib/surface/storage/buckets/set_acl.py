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
"""Implementation of buckets set-acl command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.Hidden
class SetAcl(base.Command):
  """Set an access control list for one or more buckets."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* allows you to set an access control list on one or more
      buckets. Using *{command}* entirely replaces any existing ACL on the
      bucket.

      See [Predefined ACLs](https://cloud.google.com/storage/docs/access-control/lists#predefined-acl)
      for a list of canned ACLs.

      Note: To make a bucket publicly readable, it is recommended to use
      *{parent_command} add-acl-grant*, to avoid accidentally removing OWNER
      permissions.
      """,
      'EXAMPLES':
          """
      To simply specify one of the canned ACLs:

        $ {command} gs://my-bucket --canned-acl=private

      To define fine-grained control over your data, first save the ACL to a
      file and edit the file:

        $ {parent_command} get-acl gs://my-bucket > acl.txt

      To then write any modifiations to `acl.txt` as the ACL on the bucket:

        $ {command} gs://my-bucket --file=acl.txt
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('url', nargs='+', help='The bucket URL(s) to modify.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--canned-acl',
        help='The name of a predefined ACL.')
    group.add_argument(
        '--file',
        help='A file path that contains an ACL as JSON or YAML.')

  def Run(self, args):
    del args  # Unused.
    raise NotImplementedError
