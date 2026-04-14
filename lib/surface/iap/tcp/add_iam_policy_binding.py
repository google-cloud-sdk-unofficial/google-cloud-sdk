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
"""Add IAM Policy Binding."""


from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.iap import util as iap_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
@base.Hidden
class AddIamPolicyBindingCommand(base.Command):
  """Add IAM policy binding to an IAP TCP IAM resource.

  Adds a policy binding to the IAM policy of an IAP TCP IAM resource. One
  binding
  consists of a member, a role, and an optional condition.
  See $ {parent_command} get-iam-policy for examples of how to specify an IAP
  TCP IAM resource.
  """

  detailed_help = {
      'EXAMPLES':
          """\
          See $ {parent_command} get-iam-policy for examples of how to specify
          an IAP TCP IAM resource.

          To add an IAM policy binding for the role of
          'roles/iap.tunnelResourceAccessor' for the user 'test-user@gmail.com'
          to all the Cloud Run services located in the project, run:

            $ {command} --member='user:test-user@gmail.com'
               --role='roles/iap.tunnelResourceAccessor'
               --resource-type=cloud-run

          To add an IAM policy binding for the role of
          'roles/iap.tunnelResourceAccessor' for the user 'test-user@gmail.com'
          to all the Cloud Run services located in the region 'us-west1', run:

            $ {command} --member='user:test-user@gmail.com'
               --role='roles/iap.tunnelResourceAccessor'
               --resource-type=cloud-run --region=us-west1

          To add an IAM policy binding for the role of
          'roles/iap.tunnelResourceAccessor' for the user 'test-user@gmail.com'
          in the resource 'test-resource' located in the region 'us-west1', run:

            $ {command} --member='user:test-user@gmail.com'
               --role='roles/iap.tunnelResourceAccessor'
               --resource-type=cloud-run --service=test-service --region=us-west1

          To add an IAM policy binding for the role of
          'roles/iap.tunnelResourceAccessor' for the user 'test-user@gmail.com'
          in the resource 'test-resource' located in the region 'us-west1' with
          a condition of expression='request.time < timestamp("2025-01-01T00:00:00Z")',
          title='expires_end_of_2024', and description='Expires at midnight on 2024-12-31'
          run:

            $ {command} --member='user:test-user@gmail.com'
               --role='roles/iap.tunnelResourceAccessor'
               --resource-type=cloud-run --service=test-service --region=us-west1
               --expression='request.time < timestamp("2025-01-01T00:00:00Z")'
               --title='expires_end_of_2024'
               --description='Expires at midnight on 2024-12-31'
          """,
  }

  @classmethod
  def Args(cls, parser):
    """Register flags for this command.
    """
    iap_util.AddAddIamPolicyBindingArgs(parser)
    iap_util.AddIapTcpIamResourceArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: An argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The policy binding that was added.
    """
    condition = iam_util.ValidateAndExtractConditionMutexRole(args)
    iap_tcp_ref = iap_util.ParseIapTcpIamResource(
        self.ReleaseTrack(),
        args)
    return iap_tcp_ref.AddIamPolicyBinding(args.member, args.role, condition)
