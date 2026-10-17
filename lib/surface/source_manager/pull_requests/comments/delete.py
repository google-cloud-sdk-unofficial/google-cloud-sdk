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
"""Delete Secure Source Manager pull request comment command."""

from googlecloudsdk.api_lib.securesourcemanager import pull_request_comments
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.source_manager import resource_args
from googlecloudsdk.core import log

DETAILED_HELP = {
    "DESCRIPTION": (
        """
          Delete a Secure Source Manager pull request comment.
        """
    ),
    "EXAMPLES": (
        """
            To delete a comment `123` on pull request `1` in repository `my-repo` and location `us-central1`,
            run the following command:

            $ {command} 123 --pull-request=1 --repository=my-repo --region=us-central1
        """
    ),
}


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.RegionalEndpointsSupported
class Delete(base.DeleteCommand):
  """Delete a Secure Source Manager pull request comment."""

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    resource_args.AddPullRequestCommentResourceArg(parser, "to delete")

  def Run(self, args):
    pull_request_comment_ref = args.CONCEPTS.pull_request_comment.Parse()
    client = pull_request_comments.PullRequestCommentsClient(
        location=pull_request_comment_ref.locationsId
    )
    delete_operation = client.Delete(pull_request_comment_ref)

    if args.async_:
      log.DeletedResource(
          pull_request_comment_ref.RelativeName(), is_async=True
      )
      return delete_operation

    # TODO(b/413742800): Remove the non wait logic once the LRO implemented.
    if delete_operation.done or not delete_operation.name:
      if delete_operation.error:
        raise waiter.OperationError(
            delete_operation.error.message or str(delete_operation.error)
        )
      log.DeletedResource(pull_request_comment_ref.RelativeName())
      return delete_operation

    response = client.WaitForOperation(
        client.GetOperationRef(delete_operation),
        "Waiting for pull request comment to be deleted",
        has_result=False,
    )
    log.DeletedResource(pull_request_comment_ref.RelativeName())
    return response


Delete.detailed_help = DETAILED_HELP
