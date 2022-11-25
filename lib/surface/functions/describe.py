# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Displays details of a Google Cloud Function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.functions.v1 import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions.v1.describe import command as command_v1
from googlecloudsdk.command_lib.functions.v2.describe import command as command_v2
from googlecloudsdk.core import log
import six.moves.http_client


def _CommonArgs(parser, track):
  """Registers flags for this command."""
  flags.AddFunctionResourceArg(parser, 'to describe')
  flags.AddGen2Flag(parser, track)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Display details of a Google Cloud Function."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    _CommonArgs(parser, base.ReleaseTrack.GA)

  @util.CatchHTTPErrorRaiseHTTPException
  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified function with its description and configured filter.
    """
    if flags.ShouldUseGen2():
      return command_v2.Run(args, self.ReleaseTrack())
    try:
      return command_v1.Run(args)
    except apitools_exceptions.HttpError as error:
      if error.status_code == six.moves.http_client.NOT_FOUND:
        log.debug(
            '1st Gen Cloud Function not found, looking for 2nd Gen Cloud Function ...'
        )
        return command_v2.Run(args, self.ReleaseTrack())
      raise


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(Describe):
  """Display details of a Google Cloud Function."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, base.ReleaseTrack.BETA)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(DescribeBeta):
  """Display details of a Google Cloud Function."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    _CommonArgs(parser, base.ReleaseTrack.ALPHA)
