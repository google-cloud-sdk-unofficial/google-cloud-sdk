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
"""Command for setting size of managed instance group."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base


def _AddArgs(parser, multizonal):
  """Adds args."""
  parser.add_argument('name', help='Managed instance group name.')
  parser.add_argument(
      '--size',
      required=True,
      type=int,
      help=('Target number of instances in managed instance group.'))
  if multizonal:
    scope_parser = parser.add_mutually_exclusive_group()
    utils.AddRegionFlag(
        scope_parser,
        resource_type='instance group manager',
        operation_type='resize',
        explanation=constants.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)
    utils.AddZoneFlag(
        scope_parser,
        resource_type='instance group manager',
        operation_type='resize',
        explanation=constants.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT)
  else:
    utils.AddZoneFlag(
        parser,
        resource_type='instance group manager',
        operation_type='resize')


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Resize(base_classes.BaseAsyncMutator):
  """Set managed instance group size."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, multizonal=False)

  @property
  def method(self):
    return 'Resize'

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def CreateGroupReference(self, args):
    return self.CreateZonalReference(args.name, args.zone)

  def CreateRequests(self, args):
    ref = self.CreateZonalReference(args.name, args.zone)
    return [(self.method,
             self.messages.ComputeInstanceGroupManagersResizeRequest(
                 instanceGroupManager=ref.Name(),
                 size=args.size,
                 project=self.project,
                 zone=ref.zone,))]


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ResizeAlpha(Resize,
                  instance_groups_utils.InstanceGroupReferenceMixin):
  """Set managed instance group size."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, multizonal=True)

  def CreateGroupReference(self, args):
    return self.CreateInstanceGroupReference(
        name=args.name, region=args.region, zone=args.zone)

  def CreateRequests(self, args):
    group_ref = self.CreateGroupReference(args)
    if group_ref.Collection() == 'compute.instanceGroupManagers':
      service = self.compute.instanceGroupManagers
      request = self.messages.ComputeInstanceGroupManagersResizeRequest(
          instanceGroupManager=group_ref.Name(),
          size=args.size,
          project=self.project,
          zone=group_ref.zone,)
    else:
      service = self.compute.regionInstanceGroupManagers
      request = self.messages.ComputeRegionInstanceGroupManagersResizeRequest(
          instanceGroupManager=group_ref.Name(),
          size=args.size,
          project=self.project,
          region=group_ref.region,)

    return [(service, self.method, request)]


Resize.detailed_help = {
    'brief': 'Set managed instance group size.',
    'DESCRIPTION': """
        *{command}* resize a managed instance group to a provided size.

If you resize down, the Instance Group Manager service deletes instances from
the group until the group reaches the desired size. To understand in what order
instances will be deleted, see the API documentation.

If you resize up, the service adds instances to the group using the current
instance template until the group reaches the desired size.
""",
}
ResizeAlpha.detailed_help = Resize.detailed_help
