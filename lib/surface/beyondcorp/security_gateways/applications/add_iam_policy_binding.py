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
"""Command to add an IAM policy binding to a security gateway application."""

from googlecloudsdk.api_lib.beyondcorp.app import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.beyondcorp import resource_args
from googlecloudsdk.command_lib.iam import iam_util


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class AddIamPolicyBinding(base.Command):
  r"""Add an IAM policy binding to a security gateway application.

  Adds an IAM policy binding to the given security gateway application.

    EXAMPLES
        To add an IAM policy binding for the role of
        'roles/beyondcorp.sgApplicationUser' for the user 'test-user@gmail.com'
        on a security gateway application 'my-app' under security gateway
        'my-security-gateway':

        $ {command} my-app --security-gateway=my-security-gateway \
        --member='user:test-user@gmail.com' \
        --role='roles/beyondcorp.sgApplicationUser' --location=global
  """

  @staticmethod
  def Args(parser):
    resource_args.AddApplicationResourceArg(
        parser,
        'The security gateway application for which to add the IAM policy'
        ' binding.',
    )
    iam_util.AddArgsForAddIamPolicyBinding(parser)

  def Run(self, args):
    client = api_util.GetClientInstance(self.ReleaseTrack())
    messages = client.MESSAGES_MODULE
    ref = args.CONCEPTS.application.Parse()

    # Get current policy
    get_req = messages.BeyondcorpProjectsLocationsSecurityGatewaysApplicationsGetIamPolicyRequest(
        resource=ref.RelativeName())
    policy = (
        client.projects_locations_securityGateways_applications.GetIamPolicy(
            get_req))

    # Add binding using the correct message type
    iam_util.AddBindingToIamPolicy(
        messages.GoogleIamV1Binding, policy, args.member, args.role)

    # Set updated policy
    set_req = messages.BeyondcorpProjectsLocationsSecurityGatewaysApplicationsSetIamPolicyRequest(
        resource=ref.RelativeName(),
        googleIamV1SetIamPolicyRequest=messages.GoogleIamV1SetIamPolicyRequest(
            policy=policy))
    result = (
        client.projects_locations_securityGateways_applications.SetIamPolicy(
            set_req))
    iam_util.LogSetIamPolicy(ref.Name(), 'application')
    return result
