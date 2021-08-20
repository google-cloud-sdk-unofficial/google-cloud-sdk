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
  """Create buckets for storing objects."""

  detailed_help = {
      'DESCRIPTION':
          """
      Create a new bucket.
      """,
      'EXAMPLES':
          """

      The following command creates a Cloud Storage bucket named ``my-bucket'':

        $ {command} gs://my-bucket

      The following command creates a bucket with the ``nearline'' default
      [storage class](https://cloud.google.com/storage/docs/storage-classes) in
      the ``asia'' [location](https://cloud.google.com/storage/docs/locations):

        $ {command} gs://my-bucket --storage-class=nearline --location=asia
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url', type=str, help='The URL of the bucket to create.')
    parser.add_argument(
        '--location',
        '-l',
        type=str,
        help=('[Location](https://cloud.google.com/storage/docs/locations)'
              ' for the bucket. If not specified, the location used by Cloud'
              ' Storage is ``us\'\'. A bucket\'s location cannot be changed'
              ' after creation.'))
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
        help=('Default [storage class]'
              '(https://cloud.google.com/storage/docs/storage-classes) for'
              ' the bucket. If not specified, the default storage class'
              ' used by Cloud Storage is "Standard".'))
    parser.add_argument(
        '--retention',
        help='Minimum [retention period](https://cloud.google.com'
        '/storage/docs/bucket-lock#retention-periods)'
        ' for objects stored in the bucket, for example'
        ' ``--retention-period=1Y1M1D5S\'\'. Objects added to the bucket'
        ' cannot be deleted until they\'ve been stored for the specified'
        ' length of time. Default is no retention period. Only available'
        ' for Cloud Storage using the JSON API.')

  def Run(self, args):
    resource = resource_reference.BucketResource(
        storage_url.storage_url_from_string(args.url))
    if args.location:
      resource.location = args.location
    if args.uniform_bucket_level_access:
      resource.uniform_bucket_level_access = True
    if args.storage_class:
      resource.storage_class = args.storage_class
    if args.retention:
      resource.retention_period = int(iso_duration.Duration().Parse(
          args.retention).total_seconds)

    create_bucket_task.CreateBucketTask(resource).execute()
