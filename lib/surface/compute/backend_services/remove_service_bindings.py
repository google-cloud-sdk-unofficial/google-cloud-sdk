# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command for removing service bindings to a backend service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import reference_utils
from googlecloudsdk.command_lib.compute.backend_services import flags

_DETAILED_HELP = {
    'EXAMPLES':
        """\
        To remove a service binding from a backend service, run:

          $ {command} NAME \
          --service-bindings=SERVICE_BINDING1 --global
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class RemoveServiceBindings(base.UpdateCommand):
  """Remove service bindings from a backend service."""

  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(parser)
    flags.AddServiceBindings(
        parser,
        required=True,
        help_text='List of service binding names to be removed from the backend service.'
    )

  def _GetRequest(self, client, backend_service_ref):
    return (client.apitools_client.backendServices, 'Get',
            client.messages.ComputeBackendServicesGetRequest(
                backendService=backend_service_ref.Name(),
                project=backend_service_ref.project))

  def _SetRequest(self, client, backend_service_ref, replacement):
    return (client.apitools_client.backendServices, 'Patch',
            client.messages.ComputeBackendServicesPatchRequest(
                backendService=backend_service_ref.Name(),
                backendServiceResource=replacement,
                project=backend_service_ref.project))

  def _Modify(self, backend_service_ref, args, existing):
    replacement = encoding.CopyProtoMessage(existing)

    old_bindings = replacement.serviceBindings or []
    bindings_to_remove = [
        reference_utils.BuildServiceBindingUrl(backend_service_ref.project,
                                               'global', binding_name)
        for binding_name in args.service_bindings
    ]
    replacement.serviceBindings = reference_utils.FilterReferences(
        old_bindings, bindings_to_remove)
    return replacement

  def Run(self, args):
    """Remove service bindings from the Backend Service."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    backend_service_ref = (
        flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.ResolveAsResource(
            args,
            holder.resources,
            scope_lister=compute_flags.GetDefaultScopeLister(client)))

    get_request = self._GetRequest(client, backend_service_ref)
    objects = client.MakeRequests([get_request])

    new_object = self._Modify(backend_service_ref, args, objects[0])

    cleared_fields = []
    if not new_object.serviceBindings:
      cleared_fields.append('serviceBindings')
    with client.apitools_client.IncludeFields(cleared_fields):
      return client.MakeRequests(
          [self._SetRequest(client, backend_service_ref, new_object)])
