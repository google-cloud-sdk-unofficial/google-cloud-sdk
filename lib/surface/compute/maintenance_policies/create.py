# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Create maintenance policy command."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.maintenance_policies import flags
from googlecloudsdk.command_lib.compute.maintenance_policies import util


class Create(base.CreateCommand):
  """Create a Google Compute Engine Maintenance Policy.

  *{command} creates a Maintenance Policy which specifies what kind of
  maintenance operations may be performed and when they can be performed.

  Currently Maintenance Policies are only available for instances and only
  support 1-day cycles.
  """

  @staticmethod
  def Args(parser):
    flags.MakeMaintenancePolicyArg().AddArgument(parser)
    flags.AddCommonArgs(parser)
    flags.AddCycleFrequencyArgs(parser)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    policy_ref = flags.MakeMaintenancePolicyArg().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    messages = holder.client.messages
    maintenance_policy = util.MakeMaintenancePolicy(
        policy_ref, args, messages)
    create_request = messages.ComputeMaintenancePoliciesInsertRequest(
        maintenancePolicy=maintenance_policy,
        project=policy_ref.project,
        region=policy_ref.region)

    service = holder.client.apitools_client.maintenancePolicies
    return client.MakeRequests([(service, 'Insert', create_request)])[0]
