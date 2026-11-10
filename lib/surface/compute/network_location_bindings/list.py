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
"""Command for listing network location bindings."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.network_location_bindings import flags
from googlecloudsdk.core import properties


@base.DefaultUniverseOnly
@base.RegionalEndpointsSupported
@base.ReleaseTracks(base.ReleaseTrack.PREVIEW)
class List(base.ListCommand):
  """List Google Compute Engine network location bindings."""

  detailed_help = {
      'brief': 'List Google Compute Engine network location bindings.',
      'DESCRIPTION': """\
      *{command}* lists network location bindings in the given regions of a
      project.

      If `--regions` is not specified, the `compute/region` property is used.
      """,
      'EXAMPLES': """\
      To list network location bindings in region `us-central1`, run:

        $ {command} --regions=us-central1

      To list network location bindings in multiple regions, run:

        $ {command} --regions=us-central1,europe-west4
      """,
  }

  @classmethod
  def Args(cls, parser):
    """Register flags for this command."""
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    lister.AddRegionsArgWithoutBaseArgs(parser)

  def Run(self, args):
    """Issue per-region NetworkLocationBindings LIST requests."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    # NetworkLocationBindings has no AggregatedList method, so always scope the
    # request to explicit regions. This keeps RegionalLister on per-region List
    # calls instead of falling back to AggregatedList.
    if not args.regions:
      args.regions = [properties.VALUES.compute.region.Get(required=True)]

    request_data = lister.ParseRegionalFlags(args, holder.resources)
    list_implementation = lister.RegionalLister(
        client, client.apitools_client.networkLocationBindings
    )
    return lister.Invoke(request_data, list_implementation)
