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
"""Command for stopping autoscaling of a managed instance group."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


def _IsZonalGroup(ref):
  """Checks if reference to instance group is zonal."""
  return ref.Collection() == 'compute.instanceGroupManagers'


class StopAutoscaling(base_classes.BaseAsyncMutator):
  """Stop autoscaling a managed instance group."""

  @property
  def service(self):
    return self.compute.autoscalers

  @property
  def resource_type(self):
    return 'autoscalers'

  @property
  def method(self):
    return 'Delete'

  @staticmethod
  def Args(parser):
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  def CreateGroupReference(self, args):
    resource_arg = instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
    default_scope = compute_scope.ScopeEnum.ZONE
    scope_lister = flags.GetDefaultScopeLister(
        self.compute_client, self.project)
    return resource_arg.ResolveAsResource(
        args, self.resources, default_scope=default_scope,
        scope_lister=scope_lister)

  def GetAutoscalerServiceForGroup(self, group_ref):
    if _IsZonalGroup(group_ref):
      return self.compute.autoscalers
    else:
      return self.compute.regionAutoscalers

  def ScopeRequest(self, request, igm_ref):
    if _IsZonalGroup(igm_ref):
      request.zone = igm_ref.zone
    else:
      request.region = igm_ref.region

  def GetAutoscalerResource(self, igm_ref, args):
    if _IsZonalGroup(igm_ref):
      scope_name = igm_ref.zone
      scope_type = 'zone'
      zones, regions = [scope_name], None
    else:
      scope_name = igm_ref.region
      scope_type = 'region'
      zones, regions = None, [scope_name]

    autoscaler = managed_instance_groups_utils.AutoscalerForMig(
        mig_name=args.name,
        autoscalers=managed_instance_groups_utils.AutoscalersForLocations(
            regions=regions,
            zones=zones,
            project=self.project,
            compute=self.compute,
            http=self.http,
            batch_url=self.batch_url),
        project=self.project,
        scope_name=scope_name,
        scope_type=scope_type)
    if autoscaler is None:
      raise managed_instance_groups_utils.ResourceNotFoundException(
          'The managed instance group is not autoscaled.')
    return autoscaler

  def CreateRequests(self, args):
    igm_ref = self.CreateGroupReference(args)
    service = self.GetAutoscalerServiceForGroup(igm_ref)

    # Assert that Instance Group Manager exists.
    managed_instance_groups_utils.GetInstanceGroupManagerOrThrow(
        igm_ref, self.compute_client)

    autoscaler = self.GetAutoscalerResource(igm_ref, args)
    request = service.GetRequestType(self.method)(
        project=self.project,
        autoscaler=autoscaler.name)
    self.ScopeRequest(request, igm_ref)
    return [(service, self.method, request,)]


StopAutoscaling.detailed_help = {
    'brief': 'Stop autoscaling a managed instance group',
    'DESCRIPTION': """\
        *{command}* stops autoscaling a managed instance group. If autoscaling
is not enabled for the managed instance group, this command does nothing and
will report an error.
""",
}
