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
"""Command for testing IAM permissions on external VPN gateways."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.external_vpn_gateways import flags


_EXTERNAL_VPN_GATEWAY_ARG = flags.ExternalVpnGatewayArgument()


@base.UniverseCompatible
class TestIamPermissions(base.Command):
  """Test IAM permissions for a Compute Engine external VPN gateway.

  *{command}* tests the IAM permissions that a caller has on a Compute Engine
  external VPN gateway.

  An external VPN gateway provides the information to Google Cloud about your
  on-premises side or another Cloud provider's VPN gateway.
  """

  detailed_help = {
      'EXAMPLES':
          """\
          To test whether the caller has the 'compute.externalVpnGateways.setLabels'
          permission on an external VPN gateway, run:

              $ {command} my-external-gateway --permissions=compute.externalVpnGateways.setLabels"""
  }

  @staticmethod
  def Args(parser):
    _EXTERNAL_VPN_GATEWAY_ARG.AddArgument(
        parser, operation_type='test IAM permissions for')
    parser.add_argument(
        '--permissions',
        metavar='PERMISSION',
        type=arg_parsers.ArgList(),
        required=True,
        help='Set of permissions to check for the resource.',
    )

  def Run(self, args):
    """Issues the request to test IAM permissions on an External VPN gateway."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages
    ref = _EXTERNAL_VPN_GATEWAY_ARG.ResolveAsResource(
        args, holder.resources)

    request = messages.ComputeExternalVpnGatewaysTestIamPermissionsRequest(
        project=ref.project,
        resource=ref.Name(),
        testPermissionsRequest=messages.TestPermissionsRequest(
            permissions=args.permissions),
    )

    return client.MakeRequests(
        [(client.apitools_client.externalVpnGateways, 'TestIamPermissions',
          request)])[0]

