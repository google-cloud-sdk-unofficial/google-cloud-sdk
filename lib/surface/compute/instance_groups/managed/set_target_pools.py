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
"""Command for setting target pools of managed instance group."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags


def _AddArgs(parser, multizonal):
  """Add args."""
  parser.add_argument('name', help='Managed instance group name.')
  parser.add_argument(
      '--target-pools',
      required=True,
      type=arg_parsers.ArgList(min_length=0),
      action=arg_parsers.FloatingListValuesCatcher(),
      metavar='TARGET_POOL',
      help=('Compute Engine Target Pools to add the instances to. '
            'Target Pools must be specified by name or by URL. Example: '
            '--target-pool target-pool-1,target-pool-2.'))
  if multizonal:
    scope_parser = parser.add_mutually_exclusive_group()
    flags.AddRegionFlag(
        scope_parser,
        resource_type='instance group manager',
        operation_type='set target pools',
        explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)
    flags.AddZoneFlag(
        scope_parser,
        resource_type='instance group manager',
        operation_type='set target pools',
        explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT)
  else:
    flags.AddZoneFlag(
        parser,
        resource_type='instance group manager',
        operation_type='set target pools')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SetTargetPools(base_classes.BaseAsyncMutator):
  """Set target pools of managed instance group."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, multizonal=False)

  @property
  def method(self):
    return 'SetTargetPools'

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def CreateRequests(self, args):
    ref = self.CreateZonalReference(args.name, args.zone)
    region = utils.ZoneNameToRegionName(ref.zone)
    pool_refs = self.CreateRegionalReferences(
        args.target_pools, region, resource_type='targetPools')
    pools = [pool_ref.SelfLink() for pool_ref in pool_refs]
    request = (
        self.messages.ComputeInstanceGroupManagersSetTargetPoolsRequest(
            instanceGroupManager=ref.Name(),
            instanceGroupManagersSetTargetPoolsRequest=(
                self.messages.InstanceGroupManagersSetTargetPoolsRequest(
                    targetPools=pools,
                )
            ),
            project=self.project,
            zone=ref.zone,)
    )
    return [request]


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class SetTargetPoolsAlpha(SetTargetPools):
  """Set target pools of managed instance group."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, multizonal=True)

  def CreateRequests(self, args):
    group_ref = instance_groups_utils.CreateInstanceGroupReference(
        scope_prompter=self, compute=self.compute, resources=self.resources,
        name=args.name, region=args.region, zone=args.zone)

    if group_ref.Collection() == 'compute.instanceGroupManagers':
      region = utils.ZoneNameToRegionName(group_ref.zone)
    else:
      region = group_ref.region

    pool_refs = self.CreateRegionalReferences(
        args.target_pools, region, resource_type='targetPools')
    pools = [pool_ref.SelfLink() for pool_ref in pool_refs]

    if group_ref.Collection() == 'compute.instanceGroupManagers':
      service = self.compute.instanceGroupManagers
      request = (
          self.messages.ComputeInstanceGroupManagersSetTargetPoolsRequest(
              instanceGroupManager=group_ref.Name(),
              instanceGroupManagersSetTargetPoolsRequest=(
                  self.messages.InstanceGroupManagersSetTargetPoolsRequest(
                      targetPools=pools,
                  )
              ),
              project=self.project,
              zone=group_ref.zone,)
      )
    else:
      service = self.compute.regionInstanceGroupManagers
      request = (
          self.messages.ComputeRegionInstanceGroupManagersSetTargetPoolsRequest(
              instanceGroupManager=group_ref.Name(),
              regionInstanceGroupManagersSetTargetPoolsRequest=(
                  self.messages.
                  RegionInstanceGroupManagersSetTargetPoolsRequest(
                      targetPools=pools,
                  )
              ),
              project=self.project,
              region=group_ref.region,)
      )
    return [(service, self.method, request)]


SetTargetPools.detailed_help = {
    'brief': 'Set target pools of managed instance group.',
    'DESCRIPTION': """
        *{command}* sets the target pools for an existing managed instance group.
Instances that are part of the managed instance group will be added to the
target pool automatically.

Setting a new target pool won't apply to existing instances in the group unless
they are recreated using the recreate-instances command. But any new instances
created in the managed instance group will be added to all of the provided
target pools for load balancing purposes.
""",
}
SetTargetPoolsAlpha.detailed_help = SetTargetPools.detailed_help
