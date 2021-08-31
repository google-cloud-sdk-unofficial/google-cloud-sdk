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

"""Command to list notification configs belonging to a bucket."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.Hidden
class List(base.ListCommand):
  """List the notification configs belonging to a given bucket."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* provides a list of notification configs belonging to a
      given bucket. The listed name of each notification config can be used
      with the delete sub-command to delete that specific notification config.

      For listing Object Change Notifications instead of Cloud Pub/Sub
      notification subscription configs, add a -o flag.
      """,
      'EXAMPLES':
          """
      Fetch the list of notification configs for the bucket `example-bucket`:

        $ {command} gs://example-bucket

      The same as above, but for Object Change Notifications instead of
      Cloud Pub/Sub notification subscription configs:

        $ {command} -o gs://example-bucket

      Fetch the notification configs in all buckets matching a wildcard:

        $ {command} gs://example-*

      Fetch all of the notification configs for buckets in the default project:

        $ {command} gs://*
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'path',
        nargs='+',
        help='Bucket paths. The path must begin '
             'with gs:// and may or may not contain wildcard characters.')
    parser.add_argument(
        '-o',
        '--object',
        action='store_true',
        help=('Lists Object Change Notifications instead of Cloud Pub/Sub'
              ' notification subscription configs.'))

  def Run(self, args):
    raise NotImplementedError
