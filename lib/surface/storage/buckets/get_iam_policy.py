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
"""Implementation of buckets get-iam-policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class GetIamPolicy(base.Command):
  """Get the IAM policy for a bucket."""

  detailed_help = {
      'DESCRIPTION':
          """
      Get the IAM policy for a bucket. For more information, see [Cloud
      Identity and Access
      Management](https://cloud.google.com/storage/docs/access-control/iam).
      """,
      'EXAMPLES':
          """
      To get the IAM policy for BUCKET-1:

        $ {command} gs://BUCKET-1

      To output the IAM policy for BUCKET-1 to a file:

        $ {command} gs://BUCKET-1 > policy.txt
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url',
        nargs='+',
        help='URLs for buckets whose IAM policies are being requested.')

  def Run(self, args):
    del args  # Unused.
    raise NotImplementedError
