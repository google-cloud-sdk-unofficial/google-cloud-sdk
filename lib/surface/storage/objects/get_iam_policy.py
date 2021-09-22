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
"""Implementation of objects get-iam-policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.Hidden
class GetIamPolicy(base.Command):
  """Get the access policy for an object."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* behaves similarly to *{parent_command} get-object-acl*, but
      uses the IAM policy binding syntax in the output.
      """,
      'EXAMPLES':
          """
      To get the access policy for OBJECT-1 in BUCKET-1:

        $ {command} gs://BUCKET-1/OBJECT-1

      To output the access policy for OBJECT-1 in BUCKET-1 to a file:

        $ {command} gs://BUCKET-1/OBJECT-1 > policy.txt
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url',
        nargs='+',
        help='URLs for objects whose access policies are being requested.')

  def Run(self, args):
    del args  # Unused.
    raise NotImplementedError
