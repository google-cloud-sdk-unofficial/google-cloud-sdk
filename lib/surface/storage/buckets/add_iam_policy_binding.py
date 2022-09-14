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
"""Implementation of buckets add-iam-policy-binding command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AddIamPolicyBinding(base.Command):
  """Add an IAM policy binding to a bucket."""

  detailed_help = {
      'DESCRIPTION':
          """
      Add an IAM policy binding to a bucket. For more information, see [Cloud
      Identity and Access
      Management](https://cloud.google.com/storage/docs/access-control/iam).
      """,
      'EXAMPLES':
          """
      To grant a single role to a single principal for BUCKET-1:

        $ {command} gs://BUCKET-1 --member=user:john.doe@example.com --role=roles/storage.objectCreator

      To make objects in BUCKET-1 publicly readable:

        $ {command} gs://BUCKET-1 --member=AllUsers --role=roles/storage.objectViewer

      To specify a custom role for a principal on BUCKET-1:

        $ {command} gs://BUCKET-1 --member=user:john.doe@example.com --role=roles/customRoleName
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url',
        nargs='+',
        help='URLs for buckets that gain the IAM policy binding.')
    iam_util.AddArgsForAddIamPolicyBinding(parser)

  def Run(self, args):
    del args  # Unused.
    raise NotImplementedError
