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
"""Implementation of objects add-acl-grant command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base


class AddAclGrant(base.Command):
  """Add an access control list grant on one or more objects."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* grants a user, group, domain, or project team a role of either
      READER or OWNER on one or more objects.
      """,
      'EXAMPLES':
          """
      To grant anyone on the internet READER access to the object file.txt:

        $ {command} gs://bucket/file.txt --member=AllUsers --role=READER

      To grant members of the group admins@googlegroups.com OWNER access to
      all jpg files in example-bucket:

        $ {command} gs://example-bucket/**.jpg --member=group:admins@googlegroups.com --role=OWNER

      To grant the service account foo@developer.gserviceaccount.com OWNER
      access to the object file.txt:

        $ {command} gs://bucket/file.txt --member=user:foo@developer.gserviceaccount.com --role=OWNER

      To grant the owners of project 12345 OWNER access to the object file.txt:

        $ {command} gs://bucket/file.txt --member=project:owners-12345 --role=OWNER

      Note: You can replace `owners` with `viewers` or `editors` to grant access
      to a project's viewers/editors respectively.
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url',
        nargs='+',
        help='URLs for objects that gain the ACL grant.')
    parser.add_argument(
        '--member',
        metavar='PRINCIPAL',
        required=True,
        help=textwrap.dedent("""\
            The principal to add the grant for. Should be of the form
            `user:email` (for users or service accounts), `group:email` (for
            groups), `group:domain` or `project:team-projectId`.

            Examples: `user:test-user@gmail.com`, `group:admins@example.com`,
            `user:service-account@developer.gserviceaccount.com`,
            `group:example.domain.com` or `project:viewers-12345`.

            Can also be one of the following special values:
            * `allUsers` - anyone who is on the internet, with or without a
               Google account.
            * `allAuthenticatedUsers` - anyone who is authenticated with a
               Google account or a service account."""))
    parser.add_argument(
        '--role',
        required=True,
        choices=['READER', 'OWNER'],
        help='The role to grant.')

  def Run(self, args):
    del args  # Unused.
    raise NotImplementedError
