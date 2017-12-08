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


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class RemoveBackend(base_classes.ReadWriteCommand):
  """Remove a backend from a backend service.

  *{command}* is used to remove a backend from a backend
  service.

  Before removing a backend, it is a good idea to "drain" the
  backend first. A backend can be drained by setting its
  capacity scaler to zero through 'gcloud compute
  backend-services edit'.
  """
  _BACKEND_SERVICE_ARG = compute_flags.ResourceArgument(
      resource_name='backend service',
      completion_resource_id='compute.backendService',
      global_collection='compute.backendServices')

  @staticmethod
  def Args(parser):
    flags.GLOBAL_BACKEND_SERVICE_ARG.AddArgument(parser)
    backend_flags.AddInstanceGroup(
        parser, operation_type='remove from', multizonal=False,
        with_deprecated_zone=True)

  @property
  def service(self):
    return self.compute.backendServices

  @property
  def resource_type(self):
    return 'backendServices'

  def CreateReference(self, args):
    return flags.GLOBAL_BACKEND_SERVICE_ARG.ResolveAsResource(
        args, self.context['resources'],
        default_scope=compute_flags.ScopeEnum.GLOBAL)

  def GetGetRequest(self, args):
    return (self.service,
            'Get',
            self.messages.ComputeBackendServicesGetRequest(
                backendService=self.ref.Name(),
                project=self.project))

  def GetSetRequest(self, args, replacement, existing):
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
      raise exceptions.ToolException(
          'Backend [{0}] in zone [{1}] is not a backend of backend service '
          '[{2}].'.format(group_ref.Name(),
                          group_ref.zone,
                          args.name))
    else:
      replacement.backends.pop(backend_idx)

    return replacement


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RemoveBackendAlpha(RemoveBackend):
  """Remove a backend from a backend service.

  *{command}* is used to remove a backend from a backend
  service.

  Before removing a backend, it is a good idea to "drain" the
  backend first. A backend can be drained by setting its
  capacity scaler to zero through 'gcloud compute
  backend-services edit'.
  """

  @classmethod
  def Args(cls, parser):
    cls._BACKEND_SERVICE_ARG.AddArgument(parser)
    backend_flags.AddInstanceGroup(
        parser, operation_type='remove from', multizonal=True)

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
