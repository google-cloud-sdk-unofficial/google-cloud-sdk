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
"""Implementation of buckets remove-acl-grant command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.Hidden
class RemoveAclGrant(base.Command):
  """Remove an access control list grant on one or more buckets."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* removes a user, group, domain, or project team from the ACL on
      the given bucket. Note that unlike *{parent_command} add-acl-grant*,
      member prefixes are not required.
      """,
      'EXAMPLES':
          """
      To remove access to the bucket my-bucket for the viewers of project
      number 12345:

        $ {command} gs://my-bucket --member=viewers-12345

      To remove any current access by john.doe@example.com from the bucket
      my-bucket:

        $ {command} gs://my-bucket --member=john.doe@example.com
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url',
        nargs='+',
        help='URLs for buckets to remove access from.')
    parser.add_argument(
        '--member', required=True, help='The member to remove the grant for.')

  def Run(self, args):
    del args  # Unused.
    raise NotImplementedError
