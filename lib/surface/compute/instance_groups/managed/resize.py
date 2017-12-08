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
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.core import exceptions


def _AddArgs(parser, multizonal, creation_retries):
  """Adds args."""
  parser.add_argument('name', help='Managed instance group name.')
  parser.add_argument(
      '--size',
      required=True,
      type=int,
      help=('Target number of instances in managed instance group.'))
  if multizonal:
    scope_parser = parser.add_mutually_exclusive_group()
    flags.AddRegionFlag(
        scope_parser,
        resource_type='instance group manager',
        operation_type='resize',
        explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)
    flags.AddZoneFlag(
        scope_parser,
        resource_type='instance group manager',
        operation_type='resize',
        explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT)
  else:
    flags.AddZoneFlag(
        parser,
        resource_type='instance group manager',
        operation_type='resize')
  if creation_retries:
    parser.add_argument('--creation-retries', action='store_true', default=True,
                        help='When instance creation fails retry it.')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Resize(base_classes.BaseAsyncMutator):
  """Set managed instance group size."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, multizonal=False, creation_retries=False)

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


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ResizeBeta(Resize):
  """Set managed instance group size."""

  class ConflictingFlagsError(exceptions.Error):
    """Conflicting flags were passed."""
    pass

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, multizonal=True, creation_retries=True)

  def CreateGroupReference(self, args):
    return instance_groups_utils.CreateInstanceGroupReference(
        scope_prompter=self, compute=self.compute, resources=self.resources,
        name=args.name, region=args.region, zone=args.zone)

  def CreateRequests(self, args):
    group_ref = self.CreateGroupReference(args)
    if group_ref.Collection() == 'compute.instanceGroupManagers':
      service = self.compute.instanceGroupManagers
      method = 'ResizeAdvanced'
      request = self.messages.ComputeInstanceGroupManagersResizeAdvancedRequest(
          instanceGroupManager=group_ref.Name(),
          instanceGroupManagersResizeAdvancedRequest=(
              self.messages.InstanceGroupManagersResizeAdvancedRequest(
                  targetSize=args.size,
                  noCreationRetries=not args.creation_retries,
              )
          ),
          project=self.project,
          zone=group_ref.zone,)
    else:
      if not args.creation_retries:
        raise ConflictingFlagsError(
            'argument --no-creation-retries: not allowed with argument '
            '--region')
      service = self.compute.regionInstanceGroupManagers
      method = 'Resize'
      request = self.messages.ComputeRegionInstanceGroupManagersResizeRequest(
          instanceGroupManager=group_ref.Name(),
          size=args.size,
          project=self.project,
          region=group_ref.region,)

    return [(service, method, request)]


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
ResizeBeta.detailed_help = Resize.detailed_help
