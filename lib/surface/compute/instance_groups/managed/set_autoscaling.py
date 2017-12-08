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
"""Command for configuring autoscaling of a managed instance group."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


def _IsZonalGroup(ref):
  """Checks if reference to instance group is zonal."""
  return ref.Collection() == 'compute.instanceGroupManagers'


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class SetAutoscaling(base_classes.BaseAsyncMutator):
  """Set autoscaling parameters of a managed instance group."""

  @property
  def service(self):
    return self.compute.autoscalers

  @property
  def resource_type(self):
    return 'autoscalers'

  @property
  def method(self):
    raise exceptions.ToolException(
        'Internal error: attempted calling method before determining which '
        'method to call.')

  @staticmethod
  def Args(parser):
    managed_instance_groups_utils.AddAutoscalerArgs(
        parser=parser, queue_scaling_enabled=False)
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

  def CreateAutoscalerResource(self, igm_ref, args):
    if _IsZonalGroup(igm_ref):
      scope_name = igm_ref.zone
      scope_type = 'zone'
      zones, regions = [scope_name], None
    else:
      scope_name = igm_ref.region
      scope_type = 'region'
      zones, regions = None, [scope_name]

    autoscaler = managed_instance_groups_utils.AutoscalerForMig(
        mig_name=igm_ref.Name(),
        autoscalers=managed_instance_groups_utils.AutoscalersForLocations(
            regions=regions,
            zones=zones,
            project=self.project,
            compute=self.compute,
            http=self.http,
            batch_url=self.batch_url),
        scope_name=scope_name,
        scope_type=scope_type,
        project=self.project)
    autoscaler_name = getattr(autoscaler, 'name', None)
    new_one = autoscaler_name is None
    autoscaler_name = autoscaler_name or args.name

    if _IsZonalGroup(igm_ref):
      autoscaler_resource = managed_instance_groups_utils.BuildAutoscaler(
          args, self.messages, igm_ref, autoscaler_name, zone=scope_name)
    else:
      autoscaler_resource = managed_instance_groups_utils.BuildAutoscaler(
          args, self.messages, igm_ref, autoscaler_name, region=scope_name)
      region_link = self.resources.Parse(
          scope_name, collection='compute.regions')
      autoscaler_resource.region = region_link.SelfLink()

    return autoscaler_resource, new_one

  def ScopeRequest(self, request, igm_ref):
    if _IsZonalGroup(igm_ref):
      request.zone = igm_ref.zone
    else:
      request.region = igm_ref.region

  def CreateRequests(self, args):
    managed_instance_groups_utils.ValidateAutoscalerArgs(args)

    igm_ref = self.CreateGroupReference(args)
    service = self.GetAutoscalerServiceForGroup(igm_ref)

    # Assert that Instance Group Manager exists.
    managed_instance_groups_utils.GetInstanceGroupManagerOrThrow(
        igm_ref, self.compute_client)

    autoscaler_resource, is_new = self.CreateAutoscalerResource(igm_ref, args)

    if is_new:
      method = 'Insert'
      request = service.GetRequestType(method)(project=self.project)
      managed_instance_groups_utils.AdjustAutoscalerNameForCreation(
          autoscaler_resource)
      request.autoscaler = autoscaler_resource
    else:
      method = 'Update'
      request = service.GetRequestType(method)(project=self.project)
      request.autoscaler = autoscaler_resource.name
      request.autoscalerResource = autoscaler_resource

    self.ScopeRequest(request, igm_ref)
    return ((service, method, request),)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetAutoscalingAlpha(SetAutoscaling):
  """Set autoscaling parameters of a managed instance group."""

  @staticmethod
  def Args(parser):
    managed_instance_groups_utils.AddAutoscalerArgs(
        parser=parser, queue_scaling_enabled=True)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)


SetAutoscaling.detailed_help = {
    'brief': 'Set autoscaling parameters of a managed instance group',
    'DESCRIPTION': """\
        *{command}* sets autoscaling parameters of specified managed instance
group.

Autoscalers can use one or more policies listed below. Information on using
multiple policies can be found here: [](https://cloud.google.com/compute/docs/autoscaler/multiple-policies)
        """,
}
SetAutoscalingAlpha.detailed_help = SetAutoscaling.detailed_help
