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
"""Command to delete a Cloud Firestore ChangeStream."""

import textwrap

from googlecloudsdk.api_lib.firestore import change_streams
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.firestore import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  r"""Delete a Cloud Firestore change stream.

  ## EXAMPLES

  To delete a change stream named `my-stream` in database `my-db`:

      $ {command} my-stream --database=my-db
  """

  @staticmethod
  def Args(parser):
    flags.AddDatabaseIdFlag(parser, required=True)
    flags.AddChangeStreamIdArg(parser)
    parser.add_argument(
        "--etag",
        help=textwrap.dedent("""\
            The current etag of the change stream. If an etag is provided and
            does not match the current etag of the change stream, deletion will
            be blocked and a FAILED_PRECONDITION error will be returned.
            """),
        type=str,
    )

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    console_io.PromptContinue(
        message=(
            "The change stream 'projects/{}/databases/{}/changeStreams/{}' will"
            " be deleted.".format(project, args.database, args.change_stream)
        ),
        cancel_on_no=True,
    )
    return change_streams.DeleteChangeStream(
        project=project,
        database=args.database,
        change_stream_id=args.change_stream,
        etag=args.etag,
    )
