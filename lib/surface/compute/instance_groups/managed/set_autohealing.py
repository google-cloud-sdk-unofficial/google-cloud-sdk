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
"""Command for setting autohealing policy of managed instance group."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags


def _AddArgs(parser, multizonal):
  """Adds args."""
  parser.add_argument('name', help='Managed instance group name.')
  managed_instance_groups_utils.AddAutohealingArgs(parser)
  if multizonal:
    scope_parser = parser.add_mutually_exclusive_group()
    flags.AddRegionFlag(
        scope_parser,
        resource_type='instance group manager',
        operation_type='set autohealing policy',
        explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)
    flags.AddZoneFlag(
        scope_parser,
        resource_type='instance group manager',
        operation_type='set autohealing policy',
        explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT)
  else:
    flags.AddZoneFlag(
        parser,
        resource_type='instance group manager',
        operation_type='set autohealing policy')


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class SetAutohealing(base_classes.BaseAsyncMutator):
  """Set autohealing policy of instance group manager."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, multizonal=True)

  @property
  def method(self):
    return 'SetAutoHealingPolicies'

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  def CreateRequests(self, args):
    group_ref = instance_groups_utils.CreateInstanceGroupReference(
        scope_prompter=self, compute=self.compute, resources=self.resources,
        name=args.name, region=args.region, zone=args.zone)
    auto_healing_policies = (
        managed_instance_groups_utils.CreateAutohealingPolicies(self, args))

    if group_ref.Collection() == 'compute.instanceGroupManagers':
      service = self.compute.instanceGroupManagers
      request = (
          self.messages.
          ComputeInstanceGroupManagersSetAutoHealingPoliciesRequest(
              project=self.project,
              zone=group_ref.zone,
              instanceGroupManager=group_ref.Name(),
              instanceGroupManagersSetAutoHealingRequest=(
                  self.messages.InstanceGroupManagersSetAutoHealingRequest(
                      autoHealingPolicies=auto_healing_policies))))
    else:
      service = self.compute.regionInstanceGroupManagers
      request = (
          self.messages.
          ComputeRegionInstanceGroupManagersSetAutoHealingPoliciesRequest(
              project=self.project,
              region=group_ref.region,
              instanceGroupManager=group_ref.Name(),
              regionInstanceGroupManagersSetAutoHealingRequest=(
                  self.messages.
                  RegionInstanceGroupManagersSetAutoHealingRequest(
                      autoHealingPolicies=auto_healing_policies))))

    return [(service, self.method, request)]


SetAutohealing.detailed_help = {
    'brief': 'Set autohealing policy for managed instance group.',
    'DESCRIPTION': """
        *{command}* updates the autohealing policy for an existing managed
instance group.

If --http-health-check or --https-health-check is specified, the resulting
autohealing policy will be triggered by the health-check i.e. the autohealing
action (RECREATE) on an instance will be performed if the health-check signals
that the instance is UNHEALTHY. If neither --http-health-check nor
--https-health-check is specified, the resulting autohealing policy will be
triggered by instance's status i.e. the autohealing action (RECREATE) on an
instance will be performed if the instance.status is not RUNNING.
--initial-delay specifies the length of the period during which IGM will
refrain from autohealing the instance even if the instance is reported as not
RUNNING or UNHEALTHY. This value must be from range [0, 3600].
""",
}
