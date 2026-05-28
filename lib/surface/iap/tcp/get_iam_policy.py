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
"""Get IAM Policy."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iap import util as iap_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
@base.Hidden
class GetIamPolicyCommand(base.ListCommand):
  """Get IAM policy for an IAP TCP IAM resource.

  *{command}* displays the IAM policy associated with an IAP TCP IAM
  resource. If formatted as JSON, the output can be edited and used as a policy
  file for set-iam-policy. The output includes an "etag" field
  identifying the version emitted and allowing detection of
  concurrent policy updates; see
  $ {parent_command} set-iam-policy for additional details.
  """
  detailed_help = {
      'EXAMPLES':
          """\
          To get the IAM policy for the TCP accesses to all the Cloud Run
          services within the active project, run:

            $ {command} --resource-type=cloud-run

          To get the IAM policy for the TCP accesses to all the Cloud Run
          services in specific region, run:

            $ {command} --resource-type=cloud-run --region=REGION

          To get the IAM policy for the TCP accesses to the specific Cloud Run
          service in specific region, run:

            $ {command} --resource-type=cloud-run --service=SERVICE_ID
              --region=REGION

          """,
  }

  @classmethod
  def Args(cls, parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    iap_util.AddIapTcpIamResourceArgs(
        parser,
    )
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.
    """

    iap_tcp_ref = iap_util.ParseIapTcpIamResource(
        self.ReleaseTrack(),
        args)
    return iap_tcp_ref.GetIamPolicy()
