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
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags


def _AddArgs(parser, multizonal):
  """Adds args."""
  parser.add_argument(
      'name',
      metavar='NAME',
      completion_resource='compute.instanceGroupManagers',
      help='Managed instance group which will no longer be autoscaled.')
  if multizonal:
    scope_parser = parser.add_mutually_exclusive_group()
    flags.AddRegionFlag(
        scope_parser,
        resource_type='resources',
        operation_type='delete',
        explanation=flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)
    flags.AddZoneFlag(
        scope_parser,
        resource_type='resources',
        operation_type='delete',
        explanation=flags.ZONE_PROPERTY_EXPLANATION_NO_DEFAULT)
  else:
    flags.AddZoneFlag(
        parser,
        resource_type='resources',
        operation_type='delete')


def _IsZonalGroup(ref):
  """Checks if reference to instance group is zonal."""
  return ref.Collection() == 'compute.instanceGroupManagers'


@base.ReleaseTracks(base.ReleaseTrack.GA)
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
    _AddArgs(parser=parser, multizonal=False)

  def CreateGroupReference(self, args):
    return self.CreateZonalReference(
        args.name, args.zone, resource_type='instanceGroupManagers')

  def GetAutoscalerServiceForGroup(self, group_ref):
    return self.compute.autoscalers

  def GetAutoscalerResource(self, igm_ref, args):
    autoscaler = managed_instance_groups_utils.AutoscalerForMig(
        mig_name=args.name,
        autoscalers=managed_instance_groups_utils.AutoscalersForLocations(
            regions=None,
            zones=[igm_ref.zone],
            project=self.project,
            compute=self.compute,
            http=self.http,
            batch_url=self.batch_url),
        project=self.project,
        scope_name=igm_ref.zone,
        scope_type='zone')
    if autoscaler is None:
      raise managed_instance_groups_utils.ResourceNotFoundException(
          'The managed instance group is not autoscaled.')
    return autoscaler

  def ScopeRequest(self, request, igm_ref):
    request.zone = igm_ref.zone

  def CreateRequests(self, args):
    igm_ref = self.CreateGroupReference(args)
    service = self.GetAutoscalerServiceForGroup(igm_ref)

    managed_instance_groups_utils.AssertInstanceGroupManagerExists(
        igm_ref, self.project, self.compute, self.http, self.batch_url)

    autoscaler = self.GetAutoscalerResource(igm_ref, args)
    request = service.GetRequestType(self.method)(
        project=self.project,
        autoscaler=autoscaler.name)
    self.ScopeRequest(request, igm_ref)
    return [(service, self.method, request,)]


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class StopAutoscalingAlpha(StopAutoscaling):
  """Stop autoscaling a managed instance group."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, multizonal=True)

  def CreateGroupReference(self, args):
    return instance_groups_utils.CreateInstanceGroupReference(
        scope_prompter=self, compute=self.compute, resources=self.resources,
        name=args.name, region=args.region, zone=args.zone)

  def GetAutoscalerServiceForGroup(self, group_ref):
    if _IsZonalGroup(group_ref):
      return self.compute.autoscalers
    else:
      return self.compute.regionAutoscalers

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

  def ScopeRequest(self, request, igm_ref):
    if _IsZonalGroup(igm_ref):
      request.zone = igm_ref.zone
    else:
      request.region = igm_ref.region


StopAutoscaling.detailed_help = {
    'brief': 'Stop autoscaling a managed instance group',
    'DESCRIPTION': """\
        *{command}* stops autoscaling a managed instance group. If autoscaling
is not enabled for the managed instance group, this command does nothing and
will report an error.
""",
}
StopAutoscalingAlpha.detailed_help = StopAutoscaling.detailed_help
