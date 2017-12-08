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
"""instance-groups managed set-named-ports command.

It's an alias for the instance-groups set-named-ports command.
"""
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base


def _IsZonalGroup(group_ref):
  """Checks if group is zonal."""
  return group_ref.Collection() == 'compute.instanceGroups'


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class SetNamedPorts(instance_groups_utils.InstanceGroupSetNamedPorts):
  """Sets named ports for instance groups."""

  @staticmethod
  def Args(parser):
    instance_groups_utils.InstanceGroupSetNamedPorts.AddArgs(
        parser=parser, multizonal=False)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetNamedPortsAlpha(instance_groups_utils.InstanceGroupSetNamedPorts,
                         instance_groups_utils.InstanceGroupReferenceMixin):
  """Sets named ports for instance groups."""

  @staticmethod
  def Args(parser):
    instance_groups_utils.InstanceGroupSetNamedPorts.AddArgs(
        parser=parser, multizonal=True)

  def GetGroupReference(self, args):
    return self.CreateInstanceGroupReference(
        name=args.group, region=args.region, zone=args.zone,
        zonal_resource_type='instanceGroups',
        regional_resource_type='regionInstanceGroups')

  def GetServiceForGroup(self, group_ref):
    if _IsZonalGroup(group_ref):
      return self.compute.instanceGroups
    else:
      return self.compute.regionInstanceGroups

  def CreateRequestForGroup(self, group_ref, ports, fingerprint):
    if _IsZonalGroup(group_ref):
      request_body = self.messages.InstanceGroupsSetNamedPortsRequest(
          fingerprint=fingerprint,
          namedPorts=ports)
      return self.messages.ComputeInstanceGroupsSetNamedPortsRequest(
          instanceGroup=group_ref.Name(),
          instanceGroupsSetNamedPortsRequest=request_body,
          zone=group_ref.zone,
          project=self.project)
    else:
      request_body = self.messages.RegionInstanceGroupsSetNamedPortsRequest(
          fingerprint=fingerprint,
          namedPorts=ports)
      return self.messages.ComputeRegionInstanceGroupsSetNamedPortsRequest(
          instanceGroup=group_ref.Name(),
          regionInstanceGroupsSetNamedPortsRequest=request_body,
          region=group_ref.region,
          project=self.project)

  def GetGroupFingerprint(self, group):
    """Gets fingerprint of given instance group."""
    if _IsZonalGroup(group):
      service = self.compute.instanceGroups
      get_request = service.GetRequestType('Get')(
          instanceGroup=group.Name(),
          zone=group.zone,
          project=self.project)
    else:
      service = self.compute.regionInstanceGroups
      get_request = service.GetRequestType('Get')(
          instanceGroup=group.Name(),
          region=group.region,
          project=self.project)

    errors = []
    resources = list(request_helper.MakeRequests(
        requests=[(service, 'Get', get_request)],
        http=self.http,
        batch_url=self.batch_url,
        errors=errors,
        custom_get_requests=None))

    if errors:
      utils.RaiseException(
          errors,
          instance_groups_utils.FingerprintFetchException,
          error_message='Could not set named ports for resource:')
    return resources[0].fingerprint
