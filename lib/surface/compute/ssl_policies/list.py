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


from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.ssl_policies import flags


@base.UniverseCompatible
class List(base.ListCommand):
  """List SSL policies."""

  @classmethod
  def Args(cls, parser):
    if cls.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      parser.display_info.AddFormat(flags.ALPHA_AGGREGATED_LIST_FORMAT)
    else:
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


List.detailed_help = base_classes.GetGlobalRegionalListerHelp('SSL policies')
