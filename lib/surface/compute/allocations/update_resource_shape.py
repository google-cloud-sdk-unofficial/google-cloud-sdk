# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Command for compute allocations update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.allocations import flags
from googlecloudsdk.command_lib.compute.allocations import resource_args
from googlecloudsdk.command_lib.compute.allocations import util


class UpdateResourceShape(base.UpdateCommand):
  """Update the resource shape a Compute Engine zonal allocation."""

  detailed_help = {
      'DESCRIPTION': """\
Update the resource shape a Compute Engine zonal allocation. This command
changes the zonal allocation and the machines updated would be added to the
destination allocation.
""",
  }

  @staticmethod
  def Args(parser):
    resource_args.GetAllocationResourceArg().AddArgument(
        parser, operation_type='create')
    flags.AddUpdateFlags(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    resources = holder.resources
    allocation_ref = resource_args.GetAllocationResourceArg().ResolveAsResource(
        args,
        resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    messages = holder.client.messages
    service = holder.client.apitools_client.allocations
    update_request = self._MakeUpdateRequest(
        args,
        messages,
        allocation_ref)

    return holder.client.MakeRequests(
        [(service, 'UpdateResourceShape', update_request)])

  def _MakeUpdateRequest(self, args, messages, allocation_ref):
    prop_msg = (
        messages.
        AllocationSpecificSKUAllocationAllocatedInstanceProperties)

    resource_prop = prop_msg(
        guestAccelerators=util.MakeGuestAccelerators(
            messages, getattr(args, 'accelerator', None)),
        localSsds=util.MakeLocalSsds(
            messages, getattr(args, 'local_ssd', None)),
        machineType=args.machine_type,
        minCpuPlatform=args.min_cpu_platform)

    resource_shape_request = messages.AllocationsUpdateResourceShapeRequest(
        count=args.vm_count,
        destinationAllocation=args.destination,
        updatedResourceProperties=resource_prop,
    )

    return messages.ComputeAllocationsUpdateResourceShapeRequest(
        allocation=allocation_ref.Name(),
        allocationsUpdateResourceShapeRequest=resource_shape_request,
        project=allocation_ref.project,
        zone=allocation_ref.zone)
