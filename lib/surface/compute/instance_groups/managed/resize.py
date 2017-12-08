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
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.core import exceptions


def _AddArgs(parser, creation_retries):
  """Adds args."""
  parser.add_argument(
      '--size',
      required=True,
      type=int,
      help=('Target number of instances in managed instance group.'))

  if creation_retries:
    parser.add_argument('--creation-retries', action='store_true', default=True,
                        help='When instance creation fails retry it.')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Resize(base_classes.BaseAsyncMutator):
  """Set managed instance group size."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, creation_retries=False)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

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
    return (instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.
            ResolveAsResource(
                args, self.resources,
                default_scope=compute_scope.ScopeEnum.ZONE,
                scope_lister=flags.GetDefaultScopeLister(
                    self.compute_client, self.project)))

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


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ResizeBeta(Resize):
  """Set managed instance group size."""

  class ConflictingFlagsError(exceptions.Error):
    """Conflicting flags were passed."""
    pass

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, creation_retries=True)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

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
