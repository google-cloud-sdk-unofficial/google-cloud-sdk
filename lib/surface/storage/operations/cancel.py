# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command to cancel a storage operation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Cancel(base.Command):
  """Cancel a storage operation."""

  detailed_help = {
      'DESCRIPTION': """\
      Cancel a storage operation. Since operations are asynchronous, this
      request is best effort and may fail in cases such as when the operation
      is already complete.
      """,
      'EXAMPLES': """\
      To cancel an operation, run:

        $ {command} BUCKET OPERATION-ID
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'bucket',
        help='Name of the bucket that the operation belongs to.',
    )
    parser.add_argument(
        'operation_id', help='The ID of the operation resource.'
    )

  def Run(self, args):
    # TODO(b/291789945): Add when API function available.
    pass
