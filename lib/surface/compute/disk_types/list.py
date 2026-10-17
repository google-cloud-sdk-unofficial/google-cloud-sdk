# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for listing disk types."""


from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.PREVIEW)
class List(base.ListCommand):
  """List Compute Engine disk types."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""\
        table(
          name,
          zone.basename(),
          validDiskSize:label=VALID_DISK_SIZES
        )""")
    parser.display_info.AddUriFunc(utils.MakeGetUriFunc())
    lister.AddZonalListerArgs(parser)
    parser.display_info.AddCacheUpdater(completers.DiskTypesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseZonalFlags(args, holder.resources)

    list_implementation = lister.ZonalLister(
        client, client.apitools_client.diskTypes)

    return lister.Invoke(request_data, list_implementation)


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ListAlphaBeta(base.ListCommand):
  """List Compute Engine disk types."""

  SCOPES = (base_classes.ScopeType.regional_scope,
            base_classes.ScopeType.zonal_scope)

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
        table(
          name,
          location():label=LOCATION,
          location_scope():label=SCOPE,
          validDiskSize:label=VALID_DISK_SIZES
        )
    """)
    parser.display_info.AddUriFunc(utils.MakeGetUriFunc())
    lister.AddMultiScopeListerFlags(parser, zonal=True, regional=True)
    parser.display_info.AddCacheUpdater(completers.DiskTypesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseMultiScopeFlags(args, holder.resources)

    list_implementation = lister.MultiScopeLister(
        client,
        zonal_service=client.apitools_client.diskTypes,
        regional_service=client.apitools_client.regionDiskTypes,
        aggregation_service=client.apitools_client.diskTypes)

    return lister.Invoke(request_data, list_implementation)


List.detailed_help = base_classes.GetZonalListerHelp('disk types')
ListAlphaBeta.detailed_help = base_classes.GetMultiScopeListerHelp(
    'disk types', ListAlphaBeta.SCOPES)
