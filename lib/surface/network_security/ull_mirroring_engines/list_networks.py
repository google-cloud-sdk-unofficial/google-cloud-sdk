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
"""Command to list networks for a ULL Mirroring Engine."""

from googlecloudsdk.api_lib.network_security.ull_mirroring_engines import api
from googlecloudsdk.api_lib.util import common_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import ull_mirroring_engine_flags


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class ListNetworks(base.ListCommand):
  """List networks configured for mirroring for a Google Cloud ULL Mirroring Engine.

  ## EXAMPLES

  To list networks for a ULL Mirroring Engine named 'my-engine' in location
  'us-central1-a', run:

    $ {command} my-engine --location=us-central1-a
  """

  @classmethod
  def Args(cls, parser):
    ull_mirroring_engine_flags.AddUllMirroringEngineResource(
        parser, cls.ReleaseTrack(),
    )
    parser.display_info.AddFormat("""
        table(
          name:label=NETWORK_NAME,
          state
        )
    """)

  def Run(self, args):
    client = api.Client(self.ReleaseTrack())
    engine_ref = args.CONCEPTS.ull_mirroring_engine.Parse()

    return client.ListNetworks(
        engine_name=engine_ref.RelativeName(),
        page_size=args.page_size,
        filter_expr=args.filter,
        order_by=common_args.ParseSortByArg(args.sort_by),
    )
