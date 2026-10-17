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
"""Open Secure Source Manager pull request command."""

from googlecloudsdk.api_lib.securesourcemanager import pull_requests
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.source_manager import resource_args
from googlecloudsdk.core import log

DETAILED_HELP = {
    "DESCRIPTION": (
        """
          Open a Secure Source Manager pull request.
        """
    ),
    "EXAMPLES": (
        """
            To open a closed pull request 1 in repository `my-repo` and location `us-central1`, run the following command:

            $ {command} 1 --repository=my-repo --region=us-central1
        """
    ),
}


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.RegionalEndpointsSupported
class Open(base.Command):
  """Open a Secure Source Manager pull request."""

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    resource_args.AddPullRequestResourceArg(parser, "to open")

  def Run(self, args):
    pull_request_ref = args.CONCEPTS.pull_request.Parse()
    client = pull_requests.PullRequestsClient(
        location=pull_request_ref.locationsId
    )
    open_operation = client.Open(pull_request_ref)

    if args.async_:
      log.status.Print(
          "Open request issued for [{}].".format(
              pull_request_ref.RelativeName()
          )
      )
      return open_operation

    response = client.GetOperationResult(
        open_operation, "Waiting for pull request to be opened"
    )
    log.status.Print(
        "Open request completed for [{}].".format(
            pull_request_ref.RelativeName()
        )
    )
    return response


Open.detailed_help = DETAILED_HELP
