# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Implementation command for deleting inventory report configurations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.Command):
  """Delete an inventory report configuration."""

  detailed_help = {
      'DESCRIPTION':
          """
      Deletes an inventory report configuration.
      """,
      'EXAMPLES':
          """

      Delete an inventory report configuration in the source bucket "my-bucket",
      with the UUID "some-id":

        $ {command} gs://my-bucket some-id
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'source_bucket_url',
        help='Indicates the URL of the source bucket that contains the '
             'inventory report configuration.')
    parser.add_argument(
        'config_id',
        help='Specifies the UUID of the report configuration to delete.')

  def Run(self, args):
    raise NotImplementedError
