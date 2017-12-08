# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Command for stopping the update process of managed instance group."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


@base.Deprecate(
    is_removed=False,
    warning='This command is deprecated. Use gcloud alpha compute '
            'instance-groups managed rolling-action '
            'stop-proactive-update instead.')
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class StopUpdateInstancesAlpha(base_classes.BaseAsyncMutator):
  """Stop current proactive update instances of managed instance group."""

  @staticmethod
  def Args(parser):
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  @property
  def method(self):
    return 'Patch'

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
    igm_resource = self.messages.InstanceGroupManager(
        updatePolicy=self.messages.InstanceGroupManagerUpdatePolicy(type=(
            self.messages.InstanceGroupManagerUpdatePolicy
            .TypeValueValuesEnum.OPPORTUNISTIC)))
    if hasattr(igm_ref, 'zone'):
      service = self.compute.instanceGroupManagers
      request = self.messages.ComputeInstanceGroupManagersPatchRequest(
          project=self.project,
          zone=igm_ref.zone,
          instanceGroupManager=igm_ref.Name(),
          instanceGroupManagerResource=igm_resource)
    elif hasattr(igm_ref, 'region'):
      service = self.compute.regionInstanceGroupManagers
      request = self.messages.ComputeRegionInstanceGroupManagersPatchRequest(
          project=self.project,
          region=igm_ref.region,
          instanceGroupManager=igm_ref.Name(),
          instanceGroupManagerResource=igm_resource)
    return [(service, self.method, request)]
