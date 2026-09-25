# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Implementation of Unix-like tail command for cloud storage providers."""

import os

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.tasks.cp import streaming_download_task


def _validate_bytes_flag(value: str) -> str:
  """Validates that the --bytes flag value is a valid integer or +integer.

  Args:
    value: The raw string passed to the --bytes flag.

  Returns:
    The validated string.

  Raises:
    arg_parsers.ArgumentTypeError: If value cannot be parsed as an integer.
  """
  try:
    int(value)
    return value
  except ValueError as exc:
    raise arg_parsers.ArgumentTypeError(
        'Invalid --bytes value: {}. Must be an integer or +integer.'.format(
            value
        )
    ) from exc


def _calculate_start_byte(
    object_size: int | None, bytes_to_read: str | int
) -> int:
  """Calculates the absolute start byte position for tailing.

  Formula:
    - For +BYTES: min(object_size, max(0, int(BYTES))).
    - For BYTES: max(0, object_size - abs(int(BYTES))).
  Does not rely on negative slicing or backend offsets.

  Args:
    object_size (int|None): Total size of the source object in bytes.
    bytes_to_read (str|int): Number of bytes requested from the end of the
      object, or starting byte offset when prefixed with '+'.

  Returns:
    int: Absolute byte offset to begin reading from.
  """
  if not object_size or object_size <= 0:
    return 0
  if isinstance(bytes_to_read, str) and bytes_to_read.startswith('+'):
    return min(object_size, max(0, int(bytes_to_read[1:])))
  return max(0, object_size - abs(int(bytes_to_read)))


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Tail(base.Command):
  """Outputs the last parts (the tail) of an object to stdout."""

  hints = base.CommandHint(read_only=True)

  detailed_help = {
      'DESCRIPTION':
          """
      The tail command outputs the last B bytes of an object to stdout. It can
      also be used to monitor real time appends to an appendable object in the
      RAPID storage.
      """,
      'EXAMPLES':
          """
      The following command outputs the last 1000 bytes of an object:

        $ {command} gs://my-bucket/object

      The following command outputs the last 100 bytes of an object:

        $ {command} gs://my-bucket/object --bytes 100

      The following command continuously streams new data as it is appended to
      the appendable object:

        $ {command} gs://my-bucket/appendable-object --follow
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('url', help='The URL of the object to tail.')
    parser.add_argument(
        '--bytes',
        default='1000',
        type=_validate_bytes_flag,
        help=(
            'Output the last BYTES bytes of the object, or use +BYTES to'
            ' output starting with byte BYTES of the object (capped at object'
            ' size). Default is 1000.'
        ),
    )
    parser.add_argument(
        '--follow',
        action='store_true',
        help=(
            'Output the last B bytes of the appendable object and continuously'
            ' streams new bytes appended to the appendable object.'
        ),
    )
    flags.add_encryption_flags(parser, command_only_reads_data=True)
    flags.add_additional_headers_flag(parser)

  def Run(self, args):
    encryption_util.initialize_key_store(args)

    url_object = storage_url.storage_url_from_string(args.url)
    if not isinstance(url_object, storage_url.CloudUrl):
      raise errors.InvalidUrlError(
          'tail only works for valid cloud URLs. {} is an invalid cloud URL.'
          .format(url_object.url_string)
      )
    client = api_factory.get_api(url_object.scheme)
    resource = client.get_object_metadata(
        url_object.bucket_name,
        url_object.resource_name,
        generation=url_object.generation,
        fields_scope=cloud_api.FieldsScope.NO_ACL,
    )

    # Set up direct unbuffered stdout stream.
    stdout_stream = os.fdopen(1, 'wb', closefd=False)
    dummy_destination_resource = resource_reference.FileObjectResource(
        storage_url.FileUrl('-')
    )
    task = streaming_download_task.StreamingDownloadTask(
        source_resource=resource,
        destination_resource=dummy_destination_resource,
        download_stream=stdout_stream,
        start_byte=_calculate_start_byte(resource.size, args.bytes),
        end_byte=None,
        follow=args.follow,
    )
    task.execute()
