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
"""Update Secure Source Manager issue command."""

from googlecloudsdk.api_lib.securesourcemanager import issues
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.source_manager import resource_args
from googlecloudsdk.core import log

DETAILED_HELP = {
    "DESCRIPTION": (
        """
          Update a Secure Source Manager issue.
        """
    ),
    "EXAMPLES": (
        """
            To update the title of issue ``123'' in repository ``my-repo'' and location ``us-central1'' to ``Updated Title'', run the following command:

            $ {command} 123 --repository=my-repo --region=us-central1 --title='Updated Title'
        """
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
@base.RegionalEndpointsSupported
class Update(base.UpdateCommand):
  """Update a Secure Source Manager issue."""

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    resource_args.AddIssueResourceArg(parser, "to update")
    parser.add_argument(
        "--title",
        required=False,
        help="The title of the issue.",
    )
    parser.add_argument(
        "--body",
        required=False,
        help="The body of the issue.",
    )

  def Run(self, args):
    issue_ref = args.CONCEPTS.issue.Parse()
    client = issues.IssuesClient(location=issue_ref.locationsId)

    update_mask = []
    if args.IsSpecified("title"):
      update_mask.append("title")
    if args.IsSpecified("body"):
      update_mask.append("body")

    update_operation = client.Update(
        issue_ref,
        title=args.title,
        body=args.body,
        update_mask=update_mask,
    )

    if args.async_:
      return update_operation

    # TODO(b/413742800): Remove the non wait logic once the LRO implemented.
    if update_operation.done or not update_operation.name:
      if update_operation.error:
        raise waiter.OperationError(
            update_operation.error.message or str(update_operation.error)
        )
      log.UpdatedResource(issue_ref.RelativeName())
      return update_operation.response

    response = client.WaitForOperation(
        client.GetOperationRef(update_operation),
        "Waiting for issue to be updated",
    )
    log.UpdatedResource(issue_ref.RelativeName())
    return response


Update.detailed_help = DETAILED_HELP
