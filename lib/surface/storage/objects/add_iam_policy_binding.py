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
"""Implementation of objects add-iam-policy-binding command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AddIamPolicyBinding(base.Command):
  """Grant a principal access to an object."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* behaves similarly to *{parent_command} add_acl_grant*, but
      uses the IAM policy binding syntax.
      """,
      'EXAMPLES':
          """
      To grant full control of OBJECT-1 in BUCKET-1 to the user
      john.doe@example.com:

        $ {command} gs://BUCKET-1/OBJECT-1 --member=user:john.doe@example.com --role=roles/storage.legacyObjectOwner

      To make OBJECT-1 publicly readable:

        $ {command} gs://BUCKET-1/OBJECT-1 --member=AllUsers --role=roles/storage.legacyObjectReader

      To grant read acess of all jpg objects in BUCKET-1 to the user
      john.doe@example.com:

        $ {command} gs://BUCKET-1/**.jpg --member=user:john.doe@example.com --role=roles/storage.legacyObjectReader
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url',
        nargs='+',
        help='URLs for objects that the principal is granted access to.')
    iam_util.AddMemberFlag(parser, 'to add the binding for', False)
    parser.add_argument(
        '--role',
        required=True,
        choices=[
            'roles/storage.legacyObjectOwner',
            'roles/storage.legacyObjectReader'
        ],
        help='Role name to assign to the principal.')

  def Run(self, args):
    del args  # Unused.
    raise NotImplementedError
