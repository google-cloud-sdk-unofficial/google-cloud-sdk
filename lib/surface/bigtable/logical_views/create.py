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
"""Bigtable logical views create command."""

import textwrap

from apitools.base.py import exceptions
from googlecloudsdk.api_lib.bigtable import logical_views
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import log

HttpError = exceptions.HttpError


@base.UniverseCompatible
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class CreateLogicalView(base.CreateCommand):
  """Create a new Bigtable logical view."""

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""\
          To create a logical view, run:
            $ {command} my-logical-view-id --query="SELECT my-column-family FROM my-table"
          """),
  }

  @staticmethod
  def Args(parser):
    arguments.AddLogicalViewResourceArg(parser, 'to create')
    (arguments.ArgAdder(parser).AddViewQuery())

  def _CreateLogicalView(self, logical_view_ref, args):
    """Creates a logical view with the given arguments.

    Args:
      logical_view_ref: A resource reference of the new logical view.
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Created logical view resource object.
    """
    return logical_views.Create(logical_view_ref, args.query)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Created resource.
    """
    logical_view_ref = args.CONCEPTS.logical_view.Parse()
    try:
      result = self._CreateLogicalView(logical_view_ref, args)
    except HttpError as e:
      util.FormatErrorMessages(e)
    else:
      log.CreatedResource(logical_view_ref.Name(), kind='logical view')
      return result
