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
"""Implementation of objects remove-iam-policy-binding command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util


@base.Hidden
class RemoveIamPolicyBinding(base.Command):
  """Remove a principal from the access policy for an object."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* behaves similarly to
      *{parent_command} remove-object-acl-grant*, but uses the IAM policy
      binding syntax.
      """,
      'EXAMPLES':
          """
      To remove access equivalent to the IAM role of
      roles/storage.legacyObjectOwner for the user john.doe@example.com on
      OBJECT-1 in BUCKET-1:

        $ {command} gs://BUCKET-1/OBJECT-1 --member=user:john.doe@example.com --role=roles/storage.legacyObjectOwner
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url',
        nargs='+',
        help='URLs for objects from which to remove the principal\'s access.')
    iam_util.AddMemberFlag(parser, 'to remove the binding for', False)
    parser.add_argument(
        '--role',
        required=True,
        choices=[
            'roles/storage.legacyObjectOwner',
            'roles/storage.legacyObjectReader'
        ],
        help='The role to remove the principal from.')

  def Run(self, args):
    del args  # Unused.
    raise NotImplementedError
