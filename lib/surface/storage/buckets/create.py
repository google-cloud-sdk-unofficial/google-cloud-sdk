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
"""Implementation of create command for making buckets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.tasks.buckets import create_bucket_task
from googlecloudsdk.core.util import iso_duration


class Create(base.Command):
  """Make Cloud Storage buckets."""

  detailed_help = {
      'DESCRIPTION':
          """
      The create command creates a new bucket.
      """,
      'EXAMPLES':
          """

      Create a Google Cloud Storage bucket named "my-bucket":

        $ *{command}* gs://my-bucket

      Create a bucket with the "nearline" default storage class:

        $ *{command}* gs://my-bucket --storage-class=nearline

      Create a bucket with the location "asia". Location can only be
      specified on bucket creation:

        $ *{command}* gs://my-bucket --location=asia

      Create a bucket with uniform bucket level access turned on:

        $ *{command}* gs://my-bucket --uniform-bucket-level-access

      Create a bucket with a default object retention period of
      1 year, 1 month, 1 day, and 5 seconds. Any ISO 8601 duration string will
      work:

        $ *{command}* gs://my-bucket --retention-period=1Y1M1D5S
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url', type=str, help='Specifies the URL of the bucket to create.')
    parser.add_argument(
        '--location',
        '-l',
        type=str,
        help="Specifies the bucket's region. Default varies by cloud provider.")
    parser.add_argument(
        '--uniform-bucket-level-access',
        '-b',
        action='store_true',
        help='Turns on uniform bucket-level access setting. Default is False.')
    parser.add_argument(
        '--storage-class',
        '-c',
        '-s',
        type=str,
        help=('Specifies the bucket\'s default storage class. Default is'
              ' the cloud provider\'s "Standard" class.'))
    parser.add_argument(
        '--retention-period',
        '-retention',
        '-r',
        type=str,
        help=("Specifies the bucket's default retention period for objects."
              ' Default is no policy, which keeps objects indefinitely. Only'
              ' available for Google Cloud Storage via the JSON API.'))

  def Run(self, args):
    resource = resource_reference.BucketResource(
        storage_url.storage_url_from_string(args.url))
    if args.location:
      resource.location = args.location
    if args.uniform_bucket_level_access:
      resource.uniform_bucket_level_access = True
    if args.storage_class:
      resource.storage_class = args.storage_class
    if args.retention_period:
      resource.retention_period = int(iso_duration.Duration().Parse(
          args.retention_period).total_seconds)

    create_bucket_task.CreateBucketTask(resource).execute()
