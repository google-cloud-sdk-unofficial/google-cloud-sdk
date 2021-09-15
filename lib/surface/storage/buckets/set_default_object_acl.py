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
"""Implementation of buckets set-default-object-acl command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class SetDefaultObjectAcl(base.Command):
  """Set the default object access control list on one or more buckets."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* allows you to set the default object access control list on
      one or more buckets. Using *{command}* entirely replaces any existing
      default object ACL for the bucket.

      See [Predefined ACLs](https://cloud.google.com/storage/docs/access-control/lists#predefined-acl)
      for a list of canned ACLs.

      Setting a default object ACL on a bucket provides a convenient way to
      ensure newly uploaded objects have a specific ACL. If you don't set the
      bucket's default object ACL, it will default to ``project-private''.
      """,
      'EXAMPLES':
          """
      To simply specify one of the canned ACLs:

        $ {command} gs://bucket --canned-acl=private

      To define fine-grained control over your data, first save the ACL to a
      file and edit the file:

        $ {parent_command} get-default-object-acl gs://bucket > acl.txt

      To then write any modifiations to `acl.txt` as the default object ACL on
      the bucket:

        $ {command} gs://bucket --file=acl.txt
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
        help='A file path that contains an ACL in JSON or YAML format.')

  def Run(self, args):
    del args  # Unused.
    raise NotImplementedError
