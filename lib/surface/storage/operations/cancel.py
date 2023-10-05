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

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.core import log


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
      To cancel the operation "1234567890" on bucket "bucket", run:

        $ {command} gs://bucket 1234567890
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url',
        help=(
            'URL of the bucket that the operation belongs to.'
            ' For example, "gs://bucket"'
        ),
    )
    parser.add_argument(
        'operation_id', help='The ID of the operation resource.'
    )

  def Run(self, args):
    url_object = storage_url.storage_url_from_string(args.url)
    errors_util.raise_error_if_not_gcs_bucket(args.command_path, url_object)
    api_factory.get_api(url_object.scheme).cancel_operation(
        bucket_name=url_object.bucket_name, operation_id=args.operation_id
    )
    log.status.Print(
        'Sent cancel request for bucket {} operation {}'.format(
            url_object, args.operation_id
        )
    )
