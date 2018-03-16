# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Command for listing groups."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute.groups import flags


class List(base.ListCommand):
  """List Google Compute Engine groups."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    lister.AddBaseListerArgs(parser)
    parser.display_info.AddCacheUpdater(completers.InstanceGroupsCompleter)

  def Run(self, args):
    compute_holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    cua_holder = base_classes.ComputeUserAccountsApiHolder(self.ReleaseTrack())
    compute_client = compute_holder.client
    cua_client = cua_holder.client

    request_data = lister.ParseNamesAndRegexpFlags(args,
                                                   compute_holder.resources)

    errors = []

    for item in lister.GetGlobalResourcesDicts(
        service=cua_client.groups,
        project=list(request_data.scope_set)[0].project,
        filter_expr=request_data.filter,
        http=compute_client.apitools_client.http,
        batch_url='https://www.googleapis.com/batch/',
        errors=errors):
      yield item

    if errors:
      utils.RaiseToolException(errors)


List.detailed_help = base_classes.GetGlobalListerHelp('groups')
