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
"""Implementation of buckets get-default-object-acl command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class GetDefaultObjectAcl(base.Command):
  """Get the default object access control list of a bucket."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* gets the default object ACL text for a bucket, which you can
      save and edit for use with *{parent_command} set-default-object-acl*.
      """,
      'EXAMPLES':
          """
      To output the default object ACL for an object as JSON:

        $ {command} gs://bucket/file.txt --format=json

      To output the default object ACL for an object to a file:

        $ {command} gs://bucket/file.txt > acl.txt
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url',
        nargs='+',
        help='URLs for buckets whose default object ACLs are being requested.')

  def Run(self, args):
    del args  # Unused.
    raise NotImplementedError
