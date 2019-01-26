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
"""Command for compute allocations create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.allocations import flags
from googlecloudsdk.command_lib.compute.allocations import resource_args
from googlecloudsdk.command_lib.compute.allocations import util


class Create(base.CreateCommand):
  """Create a Compute Engine zonal allocation."""

  @staticmethod
  def Args(parser):
    resource_args.GetAllocationResourceArg().AddArgument(
        parser, operation_type='create')
    resource_args.GetCommitmentResourceArg(required=False).AddArgument(parser)
    flags.AddCreateFlags(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    resources = holder.resources
    allocation_ref = resource_args.GetAllocationResourceArg().ResolveAsResource(
        args,
        resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    messages = holder.client.messages
    project = allocation_ref.project
    create_request = self._MakeCreateRequest(args, messages, project,
                                             allocation_ref)

    service = holder.client.apitools_client.allocations
    return holder.client.MakeRequests([(service, 'Insert', create_request)])

  def _MakeCreateRequest(self, args, messages, project, allocation_ref):
    allocation = util.MakeAllocationMessageFromArgs(
        messages, args, allocation_ref)
    allocation.commitment = args.commitment
    allocation.description = args.description
    return messages.ComputeAllocationsInsertRequest(
        allocation=allocation, project=project, zone=allocation_ref.zone)
