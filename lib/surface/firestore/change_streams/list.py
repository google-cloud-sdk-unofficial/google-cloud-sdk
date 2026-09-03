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
"""Command to list Cloud Firestore ChangeStreams."""

from googlecloudsdk.api_lib.firestore import change_streams
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.firestore import flags
from googlecloudsdk.core import properties


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  r"""List change streams under a Firestore database.

  ## EXAMPLES

  To list all change streams in database `my-db`:

      $ {command} --database=my-db
  """

  @staticmethod
  def Args(parser):
    flags.AddDatabaseIdFlag(parser, required=True)

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    return change_streams.ListChangeStreams(
        project=project,
        database=args.database,
    )
