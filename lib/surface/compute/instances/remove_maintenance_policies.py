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
"""Command for removing maintenance policies to instances."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags
from googlecloudsdk.command_lib.compute.maintenance_policies import flags
from googlecloudsdk.command_lib.compute.maintenance_policies import util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class InstancesRemoveMaintenancePolicies(base.UpdateCommand):
  """Removes maintenance policies to Google Compute Engine VM instances.

    *{command}* removes maintenance policies from Google Compute
    Engine virtual instances.
  """

  @staticmethod
  def Args(parser):
    instance_flags.INSTANCE_ARG.AddArgument(
        parser, operation_type='remove maintenance policies from')
    flags.AddResourceMaintenancePolicyArgs(
        parser, 'removed from', required=True)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    instance_ref = instance_flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=instance_flags.GetInstanceZoneScopeLister(client))

    maintenance_policy_ref = util.ParseMaintenancePolicy(
        holder.resources,
        args.resource_maintenance_policies,
        project=instance_ref.project,
        region=util.GetRegionFromZone(instance_ref.zone))

    remove_request = messages.ComputeInstancesRemoveMaintenancePoliciesRequest(
        instance=instance_ref.Name(),
        project=instance_ref.project,
        zone=instance_ref.zone,
        instancesRemoveMaintenancePoliciesRequest=
        messages.InstancesRemoveMaintenancePoliciesRequest(
            maintenancePolicies=[maintenance_policy_ref.SelfLink()]))

    return client.MakeRequests([(client.apitools_client.instances,
                                 'RemoveMaintenancePolicies', remove_request)])
