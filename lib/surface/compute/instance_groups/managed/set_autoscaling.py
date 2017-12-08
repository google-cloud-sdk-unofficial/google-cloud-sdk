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
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions


def _IsZonalGroup(ref):
  """Checks if reference to instance group is zonal."""
  return ref.Collection() == 'compute.instanceGroupManagers'


@base.ReleaseTracks(base.ReleaseTrack.GA)
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
        parser=parser, multizonal_enabled=False, queue_scaling_enabled=False)

  def CreateGroupReference(self, args):
    return self.CreateZonalReference(
        args.name, args.zone, resource_type='instanceGroupManagers')

  def GetAutoscalerServiceForGroup(self, group_ref):
    return self.compute.autoscalers

  def CreateAutoscalerResource(self, igm_ref, args):
    zone = args.zone or igm_ref.zone
    autoscaler = managed_instance_groups_utils.AutoscalerForMig(
        mig_name=igm_ref.Name(),
        autoscalers=managed_instance_groups_utils.AutoscalersForLocations(
            regions=None,
            zones=[zone],
            project=self.project,
            compute=self.compute,
            http=self.http,
            batch_url=self.batch_url),
        scope_name=zone,
        scope_type='zone',
        project=self.project)
    autoscaler_name = getattr(autoscaler, 'name', None)
    as_ref = self.CreateZonalReference(autoscaler_name or args.name, zone)
    return managed_instance_groups_utils.BuildAutoscaler(
        args, self.messages, as_ref, igm_ref), autoscaler_name is None

  def ScopeRequest(self, request, igm_ref):
    request.zone = igm_ref.zone

  def CreateRequests(self, args):
    managed_instance_groups_utils.ValidateAutoscalerArgs(args)

    igm_ref = self.CreateGroupReference(args)
    service = self.GetAutoscalerServiceForGroup(igm_ref)

    managed_instance_groups_utils.AssertInstanceGroupManagerExists(
        igm_ref, self.project, self.compute, self.http, self.batch_url)

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


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SetAutoscalingBeta(SetAutoscaling):
  """Set autoscaling parameters of a managed instance group."""

  @staticmethod
  def Args(parser):
    managed_instance_groups_utils.AddAutoscalerArgs(
        parser=parser, multizonal_enabled=True, queue_scaling_enabled=False)

  def CreateGroupReference(self, args):
    return instance_groups_utils.CreateInstanceGroupReference(
        scope_prompter=self, compute=self.compute, resources=self.resources,
        name=args.name, region=args.region, zone=args.zone)

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

    if _IsZonalGroup(igm_ref):
      as_ref = self.CreateZonalReference(
          autoscaler_name or args.name, scope_name,
          resource_type='autoscalers')
    else:
      as_ref = self.CreateRegionalReference(
          autoscaler_name or args.name, scope_name,
          resource_type='regionAutoscalers')

    autoscaler_resource = managed_instance_groups_utils.BuildAutoscaler(
        args, self.messages, as_ref, igm_ref)
    if not _IsZonalGroup(igm_ref):
      region_link = self.CreateRegionalReference(
          as_ref.region, as_ref.region, resource_type='regions')
      autoscaler_resource.region = region_link.SelfLink()

    return autoscaler_resource, autoscaler_name is None

  def ScopeRequest(self, request, igm_ref):
    if _IsZonalGroup(igm_ref):
      request.zone = igm_ref.zone
    else:
      request.region = igm_ref.region


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetAutoscalingAlpha(SetAutoscalingBeta):
  """Set autoscaling parameters of a managed instance group."""

  @staticmethod
  def Args(parser):
    managed_instance_groups_utils.AddAutoscalerArgs(
        parser=parser, multizonal_enabled=True, queue_scaling_enabled=True)


SetAutoscaling.detailed_help = {
    'brief': 'Set autoscaling parameters of a managed instance group',
    'DESCRIPTION': """\
        *{command}* sets autoscaling parameters of specified managed instance
group.
        """,
}
SetAutoscalingBeta.detailed_help = SetAutoscaling.detailed_help
SetAutoscalingAlpha.detailed_help = SetAutoscaling.detailed_help
