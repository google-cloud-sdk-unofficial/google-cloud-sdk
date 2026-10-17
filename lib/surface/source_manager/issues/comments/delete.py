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
"""Delete Secure Source Manager issue comment command."""

from googlecloudsdk.api_lib.securesourcemanager import issue_comments
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.source_manager import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis.securesourcemanager.v1 import securesourcemanager_v1_messages

DETAILED_HELP = {
    "DESCRIPTION": (
        """
          Delete a Secure Source Manager issue comment.
        """
    ),
    "EXAMPLES": (
        """
            To delete a comment ``456'' on issue ``123'' in repository ``my-repo'' and location ``us-central1'', run the following command:

            $ {command} 456 --issue=123 --repository=my-repo --region=us-central1
        """
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.RegionalEndpointsSupported
@base.Hidden
class Delete(base.DeleteCommand):
  """Delete a Secure Source Manager issue comment."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.ASYNC_FLAG.AddToParser(parser)
    resource_args.AddIssueCommentResourceArg(parser, "to delete")

  def Run(
      self, args: parser_extensions.Namespace
  ) -> (
      securesourcemanager_v1_messages.Operation
      | securesourcemanager_v1_messages.Operation.ResponseValue
      | None
  ):
    issue_comment_ref = args.CONCEPTS.issue_comment.Parse()
    client = issue_comments.IssueCommentsClient(
        location=issue_comment_ref.locationsId
    )
    delete_operation = client.Delete(issue_comment_ref)

    if args.async_:
      log.DeletedResource(issue_comment_ref.RelativeName(), is_async=True)
      return delete_operation

    response = client.GetOperationResult(
        delete_operation,
        "Waiting for issue comment to be deleted",
        has_result=False,
    )
    log.DeletedResource(issue_comment_ref.RelativeName())
    return response


Delete.detailed_help = DETAILED_HELP
