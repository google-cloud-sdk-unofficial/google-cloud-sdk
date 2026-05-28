# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Command for listing snapshot groups."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base


def _CommonArgs(parser):
  """Set Common Args."""
  parser.display_info.AddFormat("""\
      table(
        name,
        status
      )""")


def _RunList(self, args):
  """Shared logic for listing snapshot groups."""
  holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
  client = holder.client

  request_data = lister.ParseNamesAndRegexpFlags(args, holder.resources)

  list_implementation = lister.GlobalLister(
      client, client.apitools_client.snapshotGroups
  )

  return lister.Invoke(request_data, list_implementation)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class ListAlpha(base.ListCommand):
  """List Compute Engine snapshot groups."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  def Run(self, args):
    return _RunList(self, args)


@base.Hidden  # Hide this command from public documentation
@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class ListBeta(base.ListCommand):
  """List Compute Engine snapshot groups."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  def Run(self, args):
    return _RunList(self, args)


ListAlpha.detailed_help = base_classes.GetGlobalListerHelp('snapshot groups')
ListBeta.detailed_help = base_classes.GetGlobalListerHelp('snapshot groups')

