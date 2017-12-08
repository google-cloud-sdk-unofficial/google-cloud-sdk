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
"""Command for deleting instances managed by managed instance group."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


class DeleteInstances(base_classes.BaseAsyncMutator):
  """Delete instances managed by managed instance group."""

  @staticmethod
  def Args(parser):
    parser.add_argument('--instances',
                        type=arg_parsers.ArgList(min_length=1),
                        metavar='INSTANCE',
                        required=True,
                        help='Names of instances to delete.')
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  @property
  def method(self):
    return 'DeleteInstances'

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
          self.messages.
          ComputeInstanceGroupManagersDeleteInstancesRequest(
              instanceGroupManager=igm_ref.Name(),
              instanceGroupManagersDeleteInstancesRequest=(
                  self.messages.InstanceGroupManagersDeleteInstancesRequest(
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
          ComputeRegionInstanceGroupManagersDeleteInstancesRequest(
              instanceGroupManager=igm_ref.Name(),
              regionInstanceGroupManagersDeleteInstancesRequest=(
                  self.messages.
                  RegionInstanceGroupManagersDeleteInstancesRequest(
                      instances=instances,
                  )
              ),
              project=self.project,
              region=igm_ref.region,
          ))

    return [(service, self.method, request)]


DeleteInstances.detailed_help = {
    'brief': 'Delete instances managed by managed instance group.',
    'DESCRIPTION': """
        *{command}* is used to deletes one or more instances from a managed
instance group. Once the instances are deleted, the size of the group is
automatically reduced to reflect the changes.

If you would like to keep the underlying virtual machines but still remove them
from the managed instance group, use the abandon-instances command instead.
""",
}
