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
"""Command for testing IAM permissions for addresses."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.addresses import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class TestIamPermissions(base.Command):
  """Test IAM permissions for a Compute Engine address."""

  detailed_help = {
      'brief': 'Test IAM permissions for a Compute Engine address.',
      'DESCRIPTION': """\
          *{command}* tests the IAM permissions that a caller has on a Compute
          Engine address.
          """,
      'EXAMPLES': """\
          To test if the caller has the `compute.addresses.get`
          permission on the regional address `my-address` in region `us-central1`,
          run:

            $ {command} my-address --region=us-central1 --permissions=compute.addresses.get

          To test if the caller has the `compute.globalAddresses.get`
          permission on the global address `my-address`, run:

            $ {command} my-address --global --permissions=compute.globalAddresses.get
          """,
  }

  ADDRESS_ARG = None

  @staticmethod
  def Args(parser):
    TestIamPermissions.ADDRESS_ARG = flags.AddressArgument(plural=False)
    TestIamPermissions.ADDRESS_ARG.AddArgument(
        parser, operation_type='test-iam-permissions'
    )
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

    address_ref = TestIamPermissions.ADDRESS_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    if address_ref.Collection() == 'compute.addresses':
      service = client.apitools_client.addresses
      request = client.messages.ComputeAddressesTestIamPermissionsRequest(
          project=address_ref.project,
          region=address_ref.region,
          resource=address_ref.Name(),
          testPermissionsRequest=client.messages.TestPermissionsRequest(
              permissions=args.permissions
          ),
      )
    else:
      service = client.apitools_client.globalAddresses
      request = client.messages.ComputeGlobalAddressesTestIamPermissionsRequest(
          project=address_ref.project,
          resource=address_ref.Name(),
          testPermissionsRequest=client.messages.TestPermissionsRequest(
              permissions=args.permissions
          ),
      )

    return client.MakeRequests([(service, 'TestIamPermissions', request)])[0]
