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

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import storage_url


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
        default=1000,
        type=int,
        help=(
            'Output the last BYTES bytes of the object, or use +BYTES to'
            ' output starting with byte BYTES of the object. Default is 1000.'
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
    if args.url:
      url_object = storage_url.storage_url_from_string(args.url)
      if not isinstance(url_object, storage_url.CloudUrl):
        raise errors.InvalidUrlError(
            'tail only works for valid cloud URLs. {} is an invalid cloud URL.'
            .format(url_object.url_string)
        )

    # TODO(b/500229519): Implement tail command execution logic.
    raise NotImplementedError('tail command is not yet implemented.')
