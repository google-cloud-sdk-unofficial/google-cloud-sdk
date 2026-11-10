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
"""List Software Delivery Trust verification authorities command."""

from googlecloudsdk.api_lib.software_delivery_trust import authorities
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.software_delivery_trust import util


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  r"""List all Software Delivery Trust verification authorities in a given location.

  ## EXAMPLES

  To list all authorities in location 'us-central1':

    $ {command} --location=us-central1
  """

  @classmethod
  def Args(cls, parser):
    util.AddLocationResourceArg(
        parser,
        'The location to list authorities in.',
        required=True,
    )
    parser.display_info.AddFormat("""\
        table(
            name.basename():label=ID,
            description,
            updateTime:label=UPDATE_TIME
        )
    """)

  def Run(self, args):
    client = authorities.AuthoritiesClient()
    location_ref = args.CONCEPTS.location.Parse()
    return client.List(
        location_ref,
        page_size=args.page_size,
        limit=args.limit,
    )
