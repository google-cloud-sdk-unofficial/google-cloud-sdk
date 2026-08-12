# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Command for testing IAM permissions for backend services."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.backend_services import flags


@base.UniverseCompatible
@base.ReleaseTracks(
    base.ReleaseTrack.GA,
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.PREVIEW,
)
class TestIamPermissions(base.Command):
  """Test IAM permissions for a Compute Engine backend service."""

  detailed_help = {
      'brief': 'Test IAM permissions for a Compute Engine backend service.',
      'DESCRIPTION': (
          """\
          *{command}* tests the IAM permissions that a caller has on a Compute
          Engine backend service.
          """
      ),
      'EXAMPLES': (
          """\
          To test if the caller has the `compute.backendServices.get`
          permission on the global backend service `my-backend-service`, run:

            $ {command} my-backend-service --global --permissions=compute.backendServices.get

          To test if the caller has the `compute.regionBackendServices.get`
          permission on the regional backend service `my-backend-service` in
          region `us-central1`, run:

            $ {command} my-backend-service --region=us-central1 --permissions=compute.regionBackendServices.get
          """
      ),
  }

  @staticmethod
  def Args(parser):
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(parser)
    parser.add_argument(
        '--permissions',
        metavar='PERMISSION',
        type=arg_parsers.ArgList(),
        required=True,
        help='The set of permissions to check for the resource.',
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    backend_service_ref = (
        flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.ResolveAsResource(
            args,
            holder.resources,
            scope_lister=compute_flags.GetDefaultScopeLister(client),
        )
    )

    test_req = client.messages.TestPermissionsRequest(
        permissions=args.permissions
    )

    if backend_service_ref.Collection() == 'compute.backendServices':
      service = client.apitools_client.backendServices
      request = client.messages.ComputeBackendServicesTestIamPermissionsRequest(
          project=backend_service_ref.project,
          resource=backend_service_ref.Name(),
          testPermissionsRequest=test_req,
      )
    else:
      service = client.apitools_client.regionBackendServices
      request = (
          client.messages.ComputeRegionBackendServicesTestIamPermissionsRequest(
              project=backend_service_ref.project,
              region=backend_service_ref.region,
              resource=backend_service_ref.Name(),
              testPermissionsRequest=test_req,
          )
      )

    return client.MakeRequests([(service, 'TestIamPermissions', request)])[0]
