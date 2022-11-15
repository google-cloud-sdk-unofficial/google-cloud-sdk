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
"""Implementation of insights inventory-reports list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage.insights.inventory_reports import insights_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import storage_url


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """Lists all inventory report configurations."""

  detailed_help = {
      'DESCRIPTION':
          """
      List Cloud Storage inventory report configurations.
      """,
      'EXAMPLES':
          """

      List all inventory report configurations in the source bucket
      "my-bucket":

        $ {command} --source=gs://my-bucket

      List all inventory report configurations with the specified destination of
      "my-destination-bucket":

        $ {command} --destination=gs://my-destination-bucket

      List buckets with JSON formatting, only returning the "displayName" field:

        $ {command} --source=gs://my-bucket --format="json(displayName)"
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--source',
        metavar='SOURCE_BUCKET_URL',
        help='Specifies URL of the source bucket that contains the inventory '
             'report configuration.')
    parser.add_argument(
        '--destination',
        metavar='DESTINATION_BUCKET_URL',
        help='Specifies URL of the destination bucket in which generated '
             'inventory reports are configured to be stored.')

  def Run(self, args):
    if args.source is None and args.destination is None:
      raise errors.Error(
          'At least one of --source or --destination is required.')

    source_bucket = storage_url.storage_url_from_string(
        args.source) if args.source is not None else None

    destination = storage_url.storage_url_from_string(
        args.destination) if args.destination is not None else None

    return insights_api.InsightsApi().list(
        source_bucket, destination, page_size=args.page_size)
