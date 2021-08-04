# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command for listing network firewall policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools
import re

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.network_firewall_policies import flags
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List Compute Engine network firewall policies.

  *{command}* is used to list network firewall policies. A network
  firewall policy is a set of rules that controls access to various resources.
  """

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    lister.AddBaseListerArgs(parser)
    parser.display_info.AddCacheUpdater(flags.NetworkFirewallPoliciesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = client.MESSAGES_MODULE

    if args.project:
      project = args.project
    else:
      project = properties.VALUES.core.project.GetOrFail()

    if args.filter:
      regions = self.GetRegions(args.filter)
      if not regions:
        # The filter is not a list of regions: continue as global request
        # and retain the filter.
        pass
      else:
        # The filter is a list of regions: clear the filter since its value
        # is not meaningful to list_pager.
        args.filter = None
        region_generators = []
        for region in regions:
          region_generators.append(
              list_pager.YieldFromList(
                  client.regionNetworkFirewallPolicies,
                  messages.ComputeRegionNetworkFirewallPoliciesListRequest(
                      project=project, region=region),
                  field='items',
                  limit=args.limit,
                  batch_size=None))
        return itertools.chain.from_iterable(region_generators)

    request = messages.ComputeNetworkFirewallPoliciesListRequest(
        project=project)
    return list_pager.YieldFromList(
        client.networkFirewallPolicies,
        request,
        field='items',
        limit=args.limit,
        batch_size=None)

  @staticmethod
  def GetRegions(pattern):
    """Validate and return matched pattern for a list of regions.

    Args:
      pattern: The string input

    Returns:
      - The list of regions, where pattern is in the following pattern:
        region: (region-1 region-2 ...)
      - None if pattern does not match.
    """
    matcher = re.compile(r'[^\S]*(\bregion[^\S]*\:)[^\S]*\((.+)\)[^\S]*')
    matches = matcher.match(pattern.strip())
    if not matches:
      return None
    return matches.group(2).split()


List.detailed_help = {
    'EXAMPLES':
        """\
    To list global network firewall policies under project
    ``my-project'', run:

      $ {command} --project=my-project

    To list regional network firewall policies under project
    ``my-project'', specify a list of regions with ``--filter'':

      $ {command} \
          --project=my-project \
          --filter="region: (region-a region-b)"
    """,
}
