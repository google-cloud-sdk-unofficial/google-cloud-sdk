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
"""Command for listing target TCP proxies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import filter_rewrite
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projection_spec


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List target TCP proxies."""

  _enable_region_target_tcp_proxy = False

  @classmethod
  def Args(cls, parser):
    if cls._enable_region_target_tcp_proxy:
      parser.display_info.AddFormat("""
          table(
            name,
            region.basename(),
            proxyHeader,
            service.basename()
          )
      """)
      lister.AddMultiScopeListerFlags(parser, regional=True, global_=True)
    else:
      parser.display_info.AddFormat("""
          table(
            name,
            proxyHeader,
            service.basename()
          )
      """)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client

    project = properties.VALUES.core.project.Get(required=True)

    display_info = args.GetDisplayInfo()
    defaults = resource_projection_spec.ProjectionSpec(
        symbols=display_info.transforms, aliases=display_info.aliases)
    args.filter, filter_expr = filter_rewrite.Rewriter().Rewrite(
        args.filter, defaults=defaults)

    if not self._enable_region_target_tcp_proxy:
      return self._ListGlobal(client, project, args, filter_expr)

    # TODO(b/229835962): switch to lister.MultiScopeLister
    #   until then emulate AggregatedList behaviour similar to
    #   third_party/py/googlecloudsdk/surface/compute/\
    #     network_firewall_policies/list.py
    global_items = []
    regional_items = []

    if args.regions:
      regional_items = (
          self._ListRegional(client, project, args, filter_expr, args.regions))
    elif getattr(args, 'global', None):
      global_items = self._ListGlobal(client, project, args, filter_expr)
    else:
      global_items = self._ListGlobal(client, project, args, filter_expr)
      all_regions = self._GetRegions(client, project)
      regional_items = (
          self._ListRegional(client, project, args, filter_expr, all_regions))

    all_items = itertools.chain(global_items, regional_items)
    if args.limit:
      all_items = itertools.islice(all_items, args.limit)
    return all_items

  def _ListGlobal(self, client, project, args, filter_expr):
    messages = client.MESSAGES_MODULE
    request = messages.ComputeTargetTcpProxiesListRequest(
        project=project, filter=filter_expr)

    return list_pager.YieldFromList(
        client.targetTcpProxies,
        request,
        field='items',
        limit=args.limit,
        batch_size=None)

  def _ListRegional(self, client, project, args, filter_expr, regions):
    messages = client.MESSAGES_MODULE
    for region in regions:
      request = messages.ComputeRegionTargetTcpProxiesListRequest(
          project=project, region=region, filter=filter_expr)
      items = list_pager.YieldFromList(
          client.regionTargetTcpProxies,
          request,
          field='items',
          limit=args.limit,
          batch_size=None)
      # yield from items
      for item in items:
        yield item

  def _GetRegions(self, client, project):
    messages = client.MESSAGES_MODULE
    request = messages.ComputeRegionsListRequest(project=project)
    regions = list_pager.YieldFromList(
        client.regions, request, field='items', batch_size=None)
    return [region.name for region in regions]


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListAlphaBeta(List):
  _enable_region_target_tcp_proxy = True


List.detailed_help = base_classes.GetGlobalListerHelp('target TCP proxies')
ListAlphaBeta.detailed_help = base_classes.GetGlobalRegionalListerHelp(
    'target TCP proxies')
