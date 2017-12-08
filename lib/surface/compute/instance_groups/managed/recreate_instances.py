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
"""Command for recreating instances managed by a managed instance group."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


def _AddArgs(parser):
  """Adds args."""
  parser.add_argument(
      '--instances',
      type=arg_parsers.ArgList(min_length=1),
      metavar='INSTANCE',
      required=True,
      help='Names of instances to recreate.')


class RecreateInstances(base_classes.BaseAsyncMutator):
  """Recreate instances managed by a managed instance group."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  @property
  def method(self):
    return 'RecreateInstances'

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def CreateRequests(self, args):
    resource_arg = instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
    default_scope = compute_scope.ScopeEnum.ZONE
    scope_lister = flags.GetDefaultScopeLister(
        self.compute_client, self.project)
    igm_ref = resource_arg.ResolveAsResource(
        args, self.resources, default_scope=default_scope,
        scope_lister=scope_lister)
    instances = instance_groups_utils.CreateInstanceReferences(
        self.resources, self.compute_client, igm_ref, args.instances)

    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      service = self.compute.instanceGroupManagers
      request = (
          self.messages.ComputeInstanceGroupManagersRecreateInstancesRequest(
              instanceGroupManager=igm_ref.Name(),
              instanceGroupManagersRecreateInstancesRequest=(
                  self.messages.InstanceGroupManagersRecreateInstancesRequest(
                      instances=instances,
                  )
              ),
              project=self.project,
              zone=igm_ref.zone,
          ))
    else:
      service = self.compute.regionInstanceGroupManagers
      request = (
          self.messages.
          ComputeRegionInstanceGroupManagersRecreateInstancesRequest(
              instanceGroupManager=igm_ref.Name(),
              regionInstanceGroupManagersRecreateRequest=(
                  self.messages.RegionInstanceGroupManagersRecreateRequest(
                      instances=instances,)
              ),
              project=self.project,
              region=igm_ref.region,
          ))

    return [(service, self.method, request)]


RecreateInstances.detailed_help = {
    'brief': 'Recreate instances managed by a managed instance group.',
    'DESCRIPTION': """
        *{command}* is used to recreate one or more instances in a managed
instance group. The underlying virtual machine instances are deleted and
recreated based on the latest instance template configured for the managed
instance group.
""",
}
