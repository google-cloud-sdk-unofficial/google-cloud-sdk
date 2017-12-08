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
"""Command for abandoning instances owned by a managed instance group."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags


def _AddArgs(parser, multizonal):
  """Adds args."""
  parser.add_argument('name',
                      help='The managed instance group name.')
  parser.add_argument(
      '--instances',
      type=arg_parsers.ArgList(min_length=1),
      action=arg_parsers.FloatingListValuesCatcher(),
      metavar='INSTANCE',
      required=True,
      help='Names of instances to abandon.')
  if multizonal:
    scope_parser = parser.add_mutually_exclusive_group()
    flags.AddRegionFlag(
        scope_parser,
        resource_type='instance group',
        operation_type='abandon instances',
        explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)
    flags.AddZoneFlag(
        scope_parser,
        resource_type='instance group manager',
        operation_type='abandon instances',
        explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT)
  else:
    flags.AddZoneFlag(
        parser,
        resource_type='instance group manager',
        operation_type='abandon instances')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class AbandonInstances(base_classes.BaseAsyncMutator):
  """Abandon instances owned by a managed instance group."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, multizonal=False)

  @property
  def method(self):
    return 'AbandonInstances'

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def CreateRequests(self, args):
    zone_ref = self.CreateZonalReference(args.name, args.zone)
    instance_refs = self.CreateZonalReferences(
        args.instances,
        zone_ref.zone,
        resource_type='instances')
    instances = [instance_ref.SelfLink() for instance_ref in instance_refs]
    return [(self.method,
             self.messages.ComputeInstanceGroupManagersAbandonInstancesRequest(
                 instanceGroupManager=zone_ref.Name(),
                 instanceGroupManagersAbandonInstancesRequest=(
                     self.messages.InstanceGroupManagersAbandonInstancesRequest(
                         instances=instances,
                     )
                 ),
                 project=self.project,
                 zone=zone_ref.zone,
             ),),]


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class AbandonInstancesAlpha(base_classes.BaseAsyncMutator):
  """Abandon instances owned by a managed instance group."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, multizonal=True)

  @property
  def method(self):
    return 'AbandonInstances'

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def CreateRequests(self, args):
    group_ref = instance_groups_utils.CreateInstanceGroupReference(
        scope_prompter=self, compute=self.compute, resources=self.resources,
        name=args.name, region=args.region, zone=args.zone)
    instances = instance_groups_utils.CreateInstanceReferences(
        self, self.compute_client, group_ref, args.instances)

    if group_ref.Collection() == 'compute.instanceGroupManagers':
      service = self.compute.instanceGroupManagers
      request = (
          self.messages.
          ComputeInstanceGroupManagersAbandonInstancesRequest(
              instanceGroupManager=group_ref.Name(),
              instanceGroupManagersAbandonInstancesRequest=(
                  self.messages.InstanceGroupManagersAbandonInstancesRequest(
                      instances=instances,
                  )
              ),
              project=self.project,
              zone=group_ref.zone,
          ))
    else:
      service = self.compute.regionInstanceGroupManagers
      request = (
          self.messages.
          ComputeRegionInstanceGroupManagersAbandonInstancesRequest(
              instanceGroupManager=group_ref.Name(),
              regionInstanceGroupManagersAbandonInstancesRequest=(
                  self.messages.
                  RegionInstanceGroupManagersAbandonInstancesRequest(
                      instances=instances,
                  )
              ),
              project=self.project,
              region=group_ref.region,
          ))

    return [(service, self.method, request)]


AbandonInstances.detailed_help = {
    'brief': 'Abandon instances owned by a managed instance group.',
    'DESCRIPTION': """
        *{command}* abandons one or more instances from a managed instance
group, thereby reducing the targetSize of the group. Once instances have been
abandoned, the currentSize of the group is automatically reduced as well to
reflect the change.

Abandoning an instance does not delete the underlying virtual machine instances,
but just removes the instances from the instance group. If you would like the
delete the underlying instances, use the delete-instances command instead.
""",
}
AbandonInstancesAlpha.detailed_help = AbandonInstances.detailed_help
