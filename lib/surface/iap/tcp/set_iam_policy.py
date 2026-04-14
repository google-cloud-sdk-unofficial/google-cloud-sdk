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
"""Set IAM Policy."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iap import util as iap_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
@base.Hidden
class SetIamPolicyCommand(base.Command):
  """Set the IAM policy for an IAP TCP IAM resource.

  This command replaces the existing IAM policy for an IAP TCP IAM resource,
  given a file encoded in JSON or YAML that contains the IAM policy. If the
  given policy file specifies an "etag" value, then the replacement will succeed
  only if the policy already in place matches that etag. (An etag obtained via
  $ {parent_command} get-iam-policy will prevent the replacement if
  the policy for the resource has been subsequently updated.) A policy
  file that does not contain an etag value will replace any existing policy for
  the resource.
  """
  detailed_help = {
      'EXAMPLES':
          """\
          To set the IAM policy for the TCP accesses to all the Cloud Run
          services within the active project, run:

            $ {command} POLICY_FILE --resource-type=cloud-run

          To set the IAM policy for the TCP accesses to all the Cloud Run
          services in specific region, run:

            $ {command} POLICY_FILE --resource-type=cloud-run --region=REGION

          To set the IAM policy for the TCP accesses to a specific Cloud Run
          service in specific region, run:

            $ {command} POLICY_FILE --resource-type=cloud-run --service=SERVICE_ID
              --region=REGION
          """,
  }

  @classmethod
  def Args(cls, parser):
    """Register flags for this command.
    """
    iap_util.AddIAMPolicyFileArg(parser)
    iap_util.AddIapTcpIamResourceArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: An argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The policy that was set.
    """
    iap_tcp_ref = iap_util.ParseIapTcpIamResource(
        self.ReleaseTrack(),
        args)
    return iap_tcp_ref.SetIamPolicy(args.policy_file)

