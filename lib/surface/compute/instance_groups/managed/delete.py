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

"""Command for deleting managed instance group."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.api_lib.compute import path_simplifier
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags


def _AddArgs(parser, multizonal):
  """Adds args."""
  parser.add_argument(
      'names',
      metavar='NAME',
      nargs='+',
      completion_resource='compute.instanceGroupManagers',
      list_command_path=None,
      help='The resources to delete.')
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


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base_classes.ZonalDeleter):
  """Delete Google Compute Engine managed instance group."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, multizonal=False)

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def resource_type(self):
    return 'instanceGroupManagers'

  def _GenerateAutoscalerDeleteRequests(self, mig_requests):
    """Generates Delete requestes for autoscalers attached to instance groups.

    Args:
      mig_requests: Messages which will be sent to delete instance group
        managers.

    Returns:
      Messages, which will be sent to delete autoscalers.
    """
    migs = [(request.instanceGroupManager, 'zone', request.zone)
            for request in mig_requests]
    zones = sorted(set(zip(*migs)[2]))
    autoscalers_to_delete = managed_instance_groups_utils.AutoscalersForMigs(
        migs=migs,
        autoscalers=managed_instance_groups_utils.AutoscalersForZones(
            zones=zones,
            project=self.project,
            compute=self.compute,
            http=self.http,
            batch_url=self.batch_url),
        project=self.project)
    requests = []
    for autoscaler in autoscalers_to_delete:
      as_ref = self.CreateZonalReference(autoscaler.name, autoscaler.zone)
      request = self.messages.ComputeAutoscalersDeleteRequest(
          project=self.project)
      request.zone = as_ref.zone
      request.autoscaler = as_ref.Name()
      requests.append(request)
    return requests

  def Run(self, args):
    # CreateRequests() propmpts user to confirm deletion so it should be a first
    # thing to be executed in this function.
    delete_managed_instance_groups_requests = self.CreateRequests(args)
    super(Delete, self).Run(
        args,
        request_protobufs=self._GenerateAutoscalerDeleteRequests(
            mig_requests=delete_managed_instance_groups_requests),
        service=self.compute.autoscalers)
    super(Delete, self).Run(
        args, request_protobufs=delete_managed_instance_groups_requests)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class DeleteAlpha(base_classes.BaseAsyncMutator):
  """Delete Google Compute Engine managed instance group."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, multizonal=True)

  @property
  def service(self):
    return self.compute.instanceGroupManagers

  @property
  def method(self):
    return 'Delete'

  def _GenerateAutoscalerDeleteRequests(self, mig_requests):
    """Generates Delete requestes for autoscalers attached to instance groups.

    Args:
      mig_requests: Messages which will be sent to delete instance group
        managers.

    Returns:
      Messages, which will be sent to delete autoscalers.
    """
    mig_requests = zip(*mig_requests)[2] if mig_requests else []
    zone_migs = [
        (request.instanceGroupManager, 'zone', request.zone)
        for request in mig_requests
        if hasattr(request, 'zone') and request.zone is not None]
    region_migs = [
        (request.instanceGroupManager, 'region', request.region)
        for request in mig_requests
        if hasattr(request, 'region') and request.region is not None]

    zones = sorted(set(zip(*zone_migs)[2])) if zone_migs else []
    regions = sorted(set(zip(*region_migs)[2])) if region_migs else []

    autoscalers_to_delete = managed_instance_groups_utils.AutoscalersForMigs(
        migs=zone_migs + region_migs,
        autoscalers=managed_instance_groups_utils.AutoscalersForLocations(
            zones=zones,
            regions=regions,
            project=self.project,
            compute=self.compute,
            http=self.http,
            batch_url=self.batch_url),
        project=self.project)
    requests = []
    for autoscaler in autoscalers_to_delete:
      if autoscaler.zone:
        service = self.compute.autoscalers
        request = service.GetRequestType('Delete')(
            zone=path_simplifier.Name(autoscaler.zone))
      else:
        service = self.compute.regionAutoscalers
        request = service.GetRequestType('Delete')(
            region=path_simplifier.Name(autoscaler.region))

      request.autoscaler = autoscaler.name
      request.project = self.project
      requests.append((service, 'Delete', request))
    return requests

  def _GetCommonScopeNameForRefs(self, refs):
    """Gets common scope for references."""
    has_zone = any(hasattr(ref, 'zone') for ref in refs)
    has_region = any(hasattr(ref, 'region') for ref in refs)

    if has_zone and not has_region:
      return 'zone'
    elif has_region and not has_zone:
      return 'region'
    else:
      return None

  def CreateRequests(self, args):
    """Returns a list of delete messages for instance group managers."""
    # pylint:disable=too-many-function-args
    refs = instance_groups_utils.CreateInstanceGroupReferences(
        scope_prompter=self, compute=self.compute, resources=self.resources,
        names=args.names, zone=args.zone, region=args.region)
    scope_name = self._GetCommonScopeNameForRefs(refs)

    utils.PromptForDeletion(
        refs, scope_name=scope_name, prompt_title=None)

    requests = []
    for ref in refs:
      if ref.Collection() == 'compute.instanceGroupManagers':
        service = self.compute.instanceGroupManagers
        request = service.GetRequestType(self.method)(
            instanceGroupManager=ref.Name(),
            project=self.project,
            zone=ref.zone)
      else:
        service = self.compute.regionInstanceGroupManagers
        request = service.GetRequestType(self.method)(
            instanceGroupManager=ref.Name(),
            project=self.project,
            region=ref.region)

      requests.append((service, self.method, request))
    return requests

  def Run(self, args):
    # CreateRequests() propmpts user to confirm deletion so it should be a first
    # thing to be executed in this function.
    delete_managed_instance_groups_requests = self.CreateRequests(args)
    super(self.__class__, self).Run(
        args,
        request_protobufs=self._GenerateAutoscalerDeleteRequests(
            mig_requests=delete_managed_instance_groups_requests),
        service=self.compute.autoscalers)
    super(self.__class__, self).Run(
        args, request_protobufs=delete_managed_instance_groups_requests)


Delete.detailed_help = {
    'brief': 'Delete Google Compute Engine managed instance groups',
    'DESCRIPTION': """\
        *{command}* deletes one or more Google Compute Engine managed instance
groups.
        """,
}
DeleteAlpha.detailed_help = Delete.detailed_help
