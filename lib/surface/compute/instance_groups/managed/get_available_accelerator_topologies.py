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
"""Command for getting available accelerator topologies in managed instance groups."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class GetAvailableAcceleratorTopologies(base.DescribeCommand):
  """Get available accelerator topologies for a managed instance group."""

  @staticmethod
  def Args(parser):
    instance_groups_flags.MakeZonalInstanceGroupManagerArg().AddArgument(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    resource_arg = instance_groups_flags.MakeZonalInstanceGroupManagerArg()
    igm_ref = resource_arg.ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.ZONE,
        scope_lister=flags.GetDefaultScopeLister(client),
    )

    service = client.apitools_client.instanceGroupManagers
    request = client.messages.ComputeInstanceGroupManagersGetAvailableAcceleratorTopologiesRequest(
        resourceId=igm_ref.Name(),
        zone=igm_ref.zone,
        project=igm_ref.project,
    )
    return service.GetAvailableAcceleratorTopologies(request)


GetAvailableAcceleratorTopologies.detailed_help = {
    'brief': (
        'Get available accelerator topologies for a managed instance group.'
    ),
    'DESCRIPTION': (
        """\
        *{command}* gets available accelerator topologies for a managed instance group.

        Note: This command is only available to allowlisted projects/organizations
        and requires the managed instance group to be configured with a workload policy
        in raw capacity mode.
        """
    ),
    'EXAMPLES': (
        """\
        To get available accelerator topologies for a managed instance group 'my-group' in zone 'us-central1-a', run:

            $ {command} my-group --zone=us-central1-a
        """
    ),
}
