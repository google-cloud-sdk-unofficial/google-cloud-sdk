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
"""Lists Google Cloud Functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions.v1.list import command as command_v1
from googlecloudsdk.command_lib.functions.v2.list import command as command_v2


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Google Cloud Functions."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--regions',
        metavar='REGION',
        help=('Regions containing functions to list. By default, functions '
              'from the region configured in [functions/region] property are '
              'listed.'),
        type=arg_parsers.ArgList(min_length=1),
        default=['-'])
    parser.display_info.AddFormat(
        'table(name.basename():sort=1, status, trigger():label=TRIGGER, '
        'name.scope("locations").segment(0):label=REGION)')
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    return command_v1.Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(base.ListCommand):
  """List Google Cloud Functions."""

  @staticmethod
  def CommonArgs(parser, track):
    """Register flags for this command."""
    parser.add_argument(
        '--regions',
        metavar='REGION',
        help=('Regions containing functions to list. By default, functions '
              'from the region configured in [functions/region] property are '
              'listed.'),
        type=arg_parsers.ArgList(min_length=1),
        default=['-'])

    parser.display_info.AddFormat("""
        table(
          name.basename():sort=1,
          state():label=STATE,
          trigger():label=TRIGGER,
          name.scope("locations").segment(0):label=REGION,
          generation():label=ENVIRONMENT
        )
    """)

    base.URI_FLAG.RemoveFromParser(parser)

    # Add additional flags for GCFv2
    flags.AddGen2Flag(parser, track)

  @staticmethod
  def Args(parser):
    ListBeta.CommonArgs(parser, base.ReleaseTrack.BETA)

  def Run(self, args):
    if flags.ShouldUseGen2():
      return command_v2.Run(args, self.ReleaseTrack())
    else:
      return command_v1.Run(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(ListBeta):
  """List Google Cloud Functions."""

  @staticmethod
  def Args(parser):
    ListBeta.CommonArgs(parser, base.ReleaseTrack.ALPHA)
