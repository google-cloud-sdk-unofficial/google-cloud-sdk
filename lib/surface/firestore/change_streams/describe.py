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
"""Command to describe a Cloud Firestore ChangeStream."""

from googlecloudsdk.api_lib.firestore import change_streams
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.firestore import flags
from googlecloudsdk.core import properties


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  r"""Describe a Cloud Firestore change stream.

  ## EXAMPLES

  To describe a change stream named `my-stream` in database `my-db`:

      $ {command} my-stream --database=my-db
  """

  @staticmethod
  def Args(parser):
    flags.AddDatabaseIdFlag(parser, required=True)
    flags.AddChangeStreamIdArg(parser)

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    return change_streams.GetChangeStream(
        project=project,
        database=args.database,
        change_stream_id=args.change_stream,
    )
