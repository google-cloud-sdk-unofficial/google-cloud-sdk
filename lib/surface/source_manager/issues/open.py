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
"""Open Secure Source Manager issue command."""

from googlecloudsdk.api_lib.securesourcemanager import issues
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.source_manager import resource_args
from googlecloudsdk.core import log

DETAILED_HELP = {
    "DESCRIPTION": (
        """
          Open a Secure Source Manager issue.
        """
    ),
    "EXAMPLES": (
        """
            To open a closed issue ``123'' in repository ``my-repo'' and location ``us-central1'', run the following command:

            $ {command} 123 --repository=my-repo --region=us-central1
        """
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.RegionalEndpointsSupported
@base.Hidden
class Open(base.Command):
  """Open a Secure Source Manager issue."""

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    resource_args.AddIssueResourceArg(parser, "to open")
    parser.add_argument(
        "--etag",
        required=False,
        help="The current etag of the issue.",
    )

  def Run(self, args):
    issue_ref = args.CONCEPTS.issue.Parse()
    client = issues.IssuesClient(location=issue_ref.locationsId)
    open_operation = client.Open(issue_ref, etag=args.etag)

    if args.async_:
      return open_operation

    # TODO(b/413742800): Remove the non wait logic once the LRO implemented.
    if open_operation.done or not open_operation.name:
      if open_operation.error:
        raise waiter.OperationError(
            open_operation.error.message or str(open_operation.error)
        )
      log.status.Print(
          "Open request completed for [{}].".format(issue_ref.RelativeName())
      )
      return open_operation.response

    response = client.WaitForOperation(
        client.GetOperationRef(open_operation),
        "Waiting for issue to be opened",
        has_result=True,
    )
    log.status.Print(
        "Open request completed for [{}].".format(issue_ref.RelativeName())
    )
    return response


Open.detailed_help = DETAILED_HELP
