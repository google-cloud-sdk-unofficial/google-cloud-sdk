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
"""Create Secure Source Manager issue comment command."""

from googlecloudsdk.api_lib.securesourcemanager import issue_comments
from googlecloudsdk.api_lib.securesourcemanager import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.source_manager import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis.securesourcemanager.v1 import securesourcemanager_v1_messages

DETAILED_HELP = {
    "DESCRIPTION": (
        """
          Create a Secure Source Manager issue comment.
        """
    ),
    "EXAMPLES": (
        """
            To create an issue comment in issue ``123'' of repository ``my-repo'' in location ``us-central1'' with body ``My comment'', run the following command:

            $ {command} --issue=123 --repository=my-repo --region=us-central1 --body='My comment'
        """
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
@base.RegionalEndpointsSupported
class Create(base.CreateCommand):
  """Create a Secure Source Manager issue comment."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.ASYNC_FLAG.AddToParser(parser)
    resource_args.AddIssueResourceArgAsFlag(parser, "to create comment in")
    parser.add_argument(
        "--body",
        required=True,
        help="The body of the issue comment.",
    )

  def Run(
      self, args: parser_extensions.Namespace
  ) -> (
      securesourcemanager_v1_messages.Operation
      | securesourcemanager_v1_messages.Operation.ResponseValue
      | securesourcemanager_v1_messages.IssueComment
      | None
  ):
    issue_ref = args.CONCEPTS.issue.Parse()
    client = issue_comments.IssueCommentsClient(location=issue_ref.locationsId)

    create_operation = client.Create(
        issue_ref,
        args.body,
    )

    if args.async_:
      log.status.Print(
          "Create request issued for comment in issue [{}].".format(
              issue_ref.RelativeName()
          )
      )
      return create_operation

    response = client.GetOperationResult(
        create_operation, "Waiting for issue comment to be created"
    )
    comment_name = util.GetResourceNameFromResponse(response)
    if comment_name:
      log.CreatedResource(comment_name)

    return response


Create.detailed_help = DETAILED_HELP
