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

import itertools

from googlecloudsdk.api_lib.functions.v1 import util as api_util_v1
from googlecloudsdk.api_lib.functions.v2 import util as api_util_v2
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_extensions
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
    parser.display_info.AddFormat("""
        table(
          name.basename():sort=1,
          state():label=STATE,
          trigger():label=TRIGGER,
          name.scope("locations").segment(0):label=REGION,
          generation():label=ENVIRONMENT
        )""")

    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    list_v2_generator = command_v2.Run(args, self.ReleaseTrack())
    v1_regions = [r.locationId for r in api_util_v1.ListRegions()]
    # Make a copy of the args for v1 that excludes v2-only regions.
    # '-' is the default value, which corresponds to all regions.
    list_v1_args = parser_extensions.Namespace(
        limit=args.limit,
        regions=[r for r in args.regions if r == '-' or r in v1_regions])
    list_v1_generator = command_v1.Run(list_v1_args)

    # v1 autopush and staging are the same in routing perspective, they share
    # the staging-cloudfunctions endpoint. The mixer will route the request to
    # the corresponding manager instances in autopush and staging.
    # autopush-cloudfunctions.sandbox.googleapi.com endpoint is not used by v1
    # at all, the GFE will route the traffic to 2nd Gen frontend even if you
    # specified v1. it's safe to assume when user specified this override, they
    # are tending to talk to v2 only
    if api_util_v2.GetCloudFunctionsApiEnv() == api_util_v2.ApiEnv.AUTOPUSH:
      return list_v2_generator

    # respect the user overrides for all other cases.
    return itertools.chain(list_v2_generator, list_v1_generator)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """List Google Cloud Functions."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(ListBeta):
  """List Google Cloud Functions."""
