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
"""Adds an IAM policy binding to a security gateway."""

from googlecloudsdk.api_lib.beyondcorp.app import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.beyondcorp import resource_args
from googlecloudsdk.command_lib.iam import iam_util


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class AddIamPolicyBinding(base.Command):
  r"""Add an IAM policy binding to a security gateway.

  Adds an IAM policy binding to the given security gateway.

    EXAMPLES
        To add an IAM policy binding for the role of
        'roles/beyondcorp.serviceDiscoveryUser' for the user 'test-user@gmail.com'
        on a security gateway with ID 'my-security-gateway':

        $ {command} my-security-gateway --member='user:test-user@gmail.com' \
        --role='roles/beyondcorp.serviceDiscoveryUser' --location=global

        To add the same binding with a condition:

        $ {command} my-security-gateway --member='user:test-user@gmail.com' \
        --role='roles/beyondcorp.serviceDiscoveryUser' --location=global \
        --condition="expression=request.time < timestamp('2026-01-01T00:00:00Z'),title=expires_2026"
  """

  @staticmethod
  def Args(parser):
    resource_args.AddSecurityGatewayResourceArg(
        parser, 'The security gateway for which to add the IAM policy binding.'
    )
    iam_util.AddArgsForAddIamPolicyBinding(parser, add_condition=True)

  def Run(self, args):
    client = api_util.GetClientInstance(self.ReleaseTrack())
    messages = client.MESSAGES_MODULE
    ref = args.CONCEPTS.security_gateway.Parse()

    # Get current policy
    get_req = (
        messages.BeyondcorpProjectsLocationsSecurityGatewaysGetIamPolicyRequest(
            resource=ref.RelativeName(),
            options_requestedPolicyVersion=3
        )
    )
    policy = client.projects_locations_securityGateways.GetIamPolicy(get_req)

    condition = iam_util.ValidateAndExtractConditionMutexRole(args)

    # Add binding using the correct message type
    iam_util.AddBindingToIamPolicyWithCondition(
        messages.GoogleIamV1Binding,
        messages.GoogleTypeExpr,
        policy,
        args.member,
        args.role,
        condition,
    )

    if condition:
      policy.version = 3

    # Set updated policy
    set_req = messages.BeyondcorpProjectsLocationsSecurityGatewaysSetIamPolicyRequest(
        resource=ref.RelativeName(),
        googleIamV1SetIamPolicyRequest=messages.GoogleIamV1SetIamPolicyRequest(
            policy=policy))
    result = client.projects_locations_securityGateways.SetIamPolicy(set_req)
    iam_util.LogSetIamPolicy(ref.Name(), 'securityGateway')
    return result
