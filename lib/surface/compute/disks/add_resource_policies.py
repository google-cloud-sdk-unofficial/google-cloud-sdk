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
"""Command for adding resource policies to disks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils as compute_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags
from googlecloudsdk.command_lib.compute.resource_policies import flags
from googlecloudsdk.command_lib.compute.resource_policies import util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DisksAddResourcePolicies(base.UpdateCommand):
  """Add resource policies to a Google Compute Engine disk.

    *{command}* adds resource policies to a Google Compute Engine
    disk. These policies define a schedule for taking snapshots and a retention
    period for these snapshots.

    For information on how to create resource policies, see:

      $ gcloud alpha compute resource-policies create --help

  """

  @staticmethod
  def Args(parser):
    disks_flags.MakeDiskArgZonalOrRegional(plural=False).AddArgument(
        parser, operation_type='add resource policies to')
    flags.AddResourcePoliciesArgs(parser, 'added to', 'disk', required=True)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    disk_ref = disks_flags.MakeDiskArgZonalOrRegional(
        plural=False).ResolveAsResource(args, holder.resources)
    if disk_ref.Collection() == 'compute.regionDisks':
      disk_region = disk_ref.region
    else:
      disk_region = compute_utils.ZoneNameToRegionName(disk_ref.zone)

    resource_policies = []
    for policy in args.resource_policies:
      resource_policy_ref = util.ParseResourcePolicy(
          holder.resources,
          policy,
          project=disk_ref.project,
          region=disk_region)
      resource_policies.append(resource_policy_ref.SelfLink())

    if disk_ref.Collection() == 'compute.regionDisks':
      add_request = messages.ComputeRegionDisksAddResourcePoliciesRequest(
          disk=disk_ref.Name(),
          project=disk_ref.project,
          region=disk_ref.region,
          regionDisksAddResourcePoliciesRequest=
          messages.RegionDisksAddResourcePoliciesRequest(
              resourcePolicies=resource_policies))
      return client.MakeRequests([(client.apitools_client.regionDisks,
                                   'AddResourcePolicies', add_request)])
    else:
      add_request = messages.ComputeDisksAddResourcePoliciesRequest(
          disk=disk_ref.Name(),
          project=disk_ref.project,
          zone=disk_ref.zone,
          disksAddResourcePoliciesRequest=
          messages.DisksAddResourcePoliciesRequest(
              resourcePolicies=resource_policies))
      return client.MakeRequests([(client.apitools_client.disks,
                                   'AddResourcePolicies', add_request)])
