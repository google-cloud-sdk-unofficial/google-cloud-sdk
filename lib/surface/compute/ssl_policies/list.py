# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command to list SSL policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.ssl_policies import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Compute Engine SSL policies."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)

  def Run(self, args):
    """Issues the request to list all SSL policies."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = client.MESSAGES_MODULE

    project = properties.VALUES.core.project.Get(required=True)

    request = messages.ComputeSslPoliciesListRequest(
        project=project, filter=args.filter)

    return list_pager.YieldFromList(
        client.sslPolicies,
        request,
        field='items',
        limit=args.limit,
        batch_size=None)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListAlphaBeta(base.ListCommand):
  """List SSL policies."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(flags.DEFAULT_AGGREGATED_LIST_FORMAT)
    lister.AddMultiScopeListerFlags(parser, regional=True, global_=True)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseMultiScopeFlags(args, holder.resources)

    list_implementation = lister.MultiScopeLister(
        client,
        regional_service=client.apitools_client.regionSslPolicies,
        global_service=client.apitools_client.sslPolicies,
        aggregation_service=client.apitools_client.sslPolicies)

    return lister.Invoke(request_data, list_implementation)


List.detailed_help = base_classes.GetGlobalListerHelp('SSL policies')
ListAlphaBeta.detailed_help = base_classes.GetGlobalRegionalListerHelp(
    'SSL policies')
