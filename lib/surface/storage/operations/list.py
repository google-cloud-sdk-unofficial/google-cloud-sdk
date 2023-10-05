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
"""Command to list storage operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import storage_url


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List storage operations."""

  detailed_help = {
      'DESCRIPTION': """\
      List storage operations.
      """,
      'EXAMPLES': """\
      To list all storage operations that belong to the bucket "my-bucket", run:

        $ {command} gs://my-bucket

      To list operations in JSON format, run:

        $ {command} gs://my-bucket --format=json
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url',
        help='URL of the bucket that the operations belong to.',
    )

  def Run(self, args):
    url_object = storage_url.storage_url_from_string(args.url)
    errors_util.raise_error_if_not_gcs_bucket(args.command_path, url_object)
    return api_factory.get_api(url_object.scheme).list_operations(
        bucket_name=url_object.bucket_name,
    )
