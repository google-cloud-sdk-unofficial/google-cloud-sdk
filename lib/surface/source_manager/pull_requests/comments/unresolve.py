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
"""Unresolve Secure Source Manager pull request comments command."""

from googlecloudsdk.api_lib.securesourcemanager import pull_request_comments
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.source_manager import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis.securesourcemanager.v1 import securesourcemanager_v1_messages

DETAILED_HELP = {
    "DESCRIPTION": (
        """
          Unresolve comments under a Secure Source Manager pull request.
        """
    ),
    "EXAMPLES": (
        """
            To unresolve comments `comment-1`, `comment-2` in pull request `1` of repository `my-repo` and location `us-central1`, run the following command:

            $ {command} --pull-request=1 --repository=my-repo --region=us-central1 --comments=comment-1,comment-2
        """
    ),
}


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.RegionalEndpointsSupported
class Unresolve(base.Command):
  """Unresolve Secure Source Manager pull request comments."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.ASYNC_FLAG.AddToParser(parser)
    resource_args.AddPullRequestResourceArgAsFlag(
        parser, "to unresolve comments of"
    )
    parser.add_argument(
        "--comments",
        metavar="COMMENTS",
        type=arg_parsers.ArgList(),
        required=True,
        help="The list of pull request comment IDs to unresolve.",
    )
    parser.add_argument(
        "--auto-fill",
        action="store_true",
        help=(
            "If set, at least one comment in a thread is required, "
            "and rest of the comments in the same thread will be automatically "
            "updated to unresolved. If unset, all comments in the same thread "
            "need to be present."
        ),
    )

  def Run(
      self, args: parser_extensions.Namespace
  ) -> (
      securesourcemanager_v1_messages.Operation
      | securesourcemanager_v1_messages.Operation.ResponseValue
      | None
  ):
    pull_request_ref = args.CONCEPTS.pull_request.Parse()
    client = pull_request_comments.PullRequestCommentsClient(
        location=pull_request_ref.locationsId
    )
    unresolve_operation = client.Unresolve(
        pull_request_ref,
        args.comments,
        auto_fill=args.auto_fill or None,
    )

    if args.async_:
      return unresolve_operation

    # TODO(b/413742800): Remove the non wait logic once the LRO implemented.
    if unresolve_operation.done or not unresolve_operation.name:
      if unresolve_operation.error:
        raise waiter.OperationError(
            unresolve_operation.error.message or str(unresolve_operation.error)
        )
      log.status.Print(
          "Unresolve comments request completed for"
          f" [{pull_request_ref.RelativeName()}]."
      )
      return unresolve_operation

    response = client.WaitForOperation(
        client.GetOperationRef(unresolve_operation),
        "Waiting for pull request comments to be unresolved",
        has_result=False,
    )
    log.status.Print(
        "Unresolve comments request completed for"
        f" [{pull_request_ref.RelativeName()}]."
    )
    return response


Unresolve.detailed_help = DETAILED_HELP
