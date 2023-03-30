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
"""Command for listing instance templates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute.instance_templates import flags


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List Compute Engine virtual machine instance templates."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    lister.AddBaseListerArgs(parser)
    parser.display_info.AddCacheUpdater(completers.InstanceTemplatesCompleter)

  def ParseFlags(self, args, resources):
    return lister.ParseNamesAndRegexpFlags(args, resources)

  def GetListImplementation(self, client):
    return lister.GlobalLister(
        client,
        service=client.apitools_client.instanceTemplates,
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = self.ParseFlags(args, holder.resources)
    list_implementation = self.GetListImplementation(client)

    return lister.Invoke(request_data, list_implementation)


List.detailed_help = base_classes.GetGlobalListerHelp('instance templates')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(List):
  """List Compute Engine virtual machine instance templates."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    lister.AddMultiScopeListerFlags(parser, regional=True, global_=True)
    parser.display_info.AddCacheUpdater(completers.InstanceTemplatesCompleter)

  def ParseFlags(self, args, resources):
    return lister.ParseMultiScopeFlags(args, resources)

  def GetListImplementation(self, client):
    return lister.MultiScopeLister(
        client,
        regional_service=client.apitools_client.regionInstanceTemplates,
        global_service=client.apitools_client.instanceTemplates,
        aggregation_service=client.apitools_client.instanceTemplates,
    )


ListAlpha.detailed_help = base_classes.GetGlobalRegionalListerHelp(
    'instance templates'
)
