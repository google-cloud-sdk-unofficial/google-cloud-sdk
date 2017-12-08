# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Command for removing a backend from a backend service."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.backend_services import backend_flags
from googlecloudsdk.command_lib.compute.backend_services import flags
from googlecloudsdk.third_party.py27 import py27_copy as copy


@base.ReleaseTracks(base.ReleaseTrack.GA)
class RemoveBackend(base_classes.ReadWriteCommand):
  """Remove a backend from a backend service.

  *{command}* is used to remove a backend from a backend
  service.

  Before removing a backend, it is a good idea to "drain" the
  backend first. A backend can be drained by setting its
  capacity scaler to zero through 'gcloud compute
  backend-services edit'.
  """
  _BACKEND_SERVICE_ARG = flags.GLOBAL_BACKEND_SERVICE_ARG

  @classmethod
  def Args(cls, parser):
    cls._BACKEND_SERVICE_ARG.AddArgument(parser)
    backend_flags.AddInstanceGroup(
        parser, operation_type='remove from', multizonal=False,
        with_deprecated_zone=True)

  @property
  def service(self):
    if self.regional:
      return self.compute.regionBackendServices
    return self.compute.backendServices

  @property
  def resource_type(self):
    if self.regional:
      return 'regionBackendServices'
    return 'backendServices'

  def CreateReference(self, args):
    return self._BACKEND_SERVICE_ARG.ResolveAsResource(
        args, self.resources,
        default_scope=compute_flags.ScopeEnum.GLOBAL)

  def GetGetRequest(self, args):
    if self.regional:
      return (self.service,
              'Get',
              self.messages.ComputeRegionBackendServicesGetRequest(
                  backendService=self.ref.Name(),
                  region=self.ref.region,
                  project=self.project))
    return (self.service,
            'Get',
            self.messages.ComputeBackendServicesGetRequest(
                backendService=self.ref.Name(),
                project=self.project))

  def GetSetRequest(self, args, replacement, existing):
    if self.regional:
      return (self.service,
              'Update',
              self.messages.ComputeRegionBackendServicesUpdateRequest(
                  backendService=self.ref.Name(),
                  backendServiceResource=replacement,
                  region=self.ref.region,
                  project=self.project))
    return (self.service,
            'Update',
            self.messages.ComputeBackendServicesUpdateRequest(
                backendService=self.ref.Name(),
                backendServiceResource=replacement,
                project=self.project))

  def CreateGroupReference(self, args):
    return self.CreateZonalReference(
        args.instance_group,
        args.instance_group_zone,
        resource_type='instanceGroups')

  def Modify(self, args, existing):
    backend_flags.WarnOnDeprecatedFlags(args)
    replacement = copy.deepcopy(existing)

    group_ref = self.CreateGroupReference(args)

    group_uri = group_ref.SelfLink()

    backend_idx = None
    for i, backend in enumerate(existing.backends):
      if group_uri == backend.group:
        backend_idx = i

    if backend_idx is None:
      scope_value = getattr(group_ref, 'region', None)
      if scope_value is None:
        scope_value = getattr(group_ref, 'zone', None)
        scope = 'zone'
      else:
        scope = 'region'

      raise exceptions.ToolException(
          'Backend [{0}] in {1} [{2}] is not a backend of backend service '
          '[{3}].'.format(group_ref.Name(),
                          scope,
                          scope_value,
                          self.ref.Name()))
    else:
      replacement.backends.pop(backend_idx)

    return replacement

  def Run(self, args):
    # Check whether --region flag was used for regional resource.
    self.regional = getattr(args, 'region', None) is not None
    return super(RemoveBackend, self).Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class RemoveBackendBeta(RemoveBackend):
  """Remove a backend from a backend service.

  *{command}* is used to remove a backend from a backend
  service.

  Before removing a backend, it is a good idea to "drain" the
  backend first. A backend can be drained by setting its
  capacity scaler to zero through 'gcloud compute
  backend-services edit'.
  """

  _BACKEND_SERVICE_ARG = flags.GLOBAL_BACKEND_SERVICE_ARG

  @classmethod
  def Args(cls, parser):
    cls._BACKEND_SERVICE_ARG.AddArgument(parser)
    backend_flags.AddInstanceGroup(
        parser, operation_type='remove from', multizonal=True,
        with_deprecated_zone=True)

  def CreateGroupReference(self, args):
    return instance_groups_utils.CreateInstanceGroupReference(
        scope_prompter=self,
        compute=self.compute,
        resources=self.resources,
        name=args.instance_group,
        region=args.instance_group_region,
        zone=args.instance_group_zone,
        zonal_resource_type='instanceGroups',
        regional_resource_type='regionInstanceGroups')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RemoveBackendAlpha(RemoveBackendBeta):
  """Remove a backend from a backend service.

  *{command}* is used to remove a backend from a backend
  service.

  Before removing a backend, it is a good idea to "drain" the
  backend first. A backend can be drained by setting its
  capacity scaler to zero through 'gcloud compute
  backend-services edit'.
  """

  _BACKEND_SERVICE_ARG = flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG

  @classmethod
  def Args(cls, parser):
    cls._BACKEND_SERVICE_ARG.AddArgument(parser)
    backend_flags.AddInstanceGroup(
        parser, operation_type='remove from', multizonal=True)
