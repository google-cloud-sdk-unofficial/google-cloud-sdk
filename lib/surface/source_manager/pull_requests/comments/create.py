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
"""Create Secure Source Manager pull request comment command."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.securesourcemanager import pull_request_comments
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.source_manager import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

DETAILED_HELP = {
    "DESCRIPTION": (
        """
          Create a Secure Source Manager pull request comment.
        """
    ),
    "EXAMPLES": (
        """
            To create a comment in pull request `1` of repository `my-repo` in location `us-central1` with body `My comment`, run the following command:

            $ {command} --pull-request=1 --repository=my-repo --region=us-central1 --body='My comment'
        """
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.RegionalEndpointsSupported
class Create(base.CreateCommand):
  """Create a Secure Source Manager pull request comment."""

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    resource_args.AddPullRequestResourceArgAsFlag(
        parser, "to create comment in"
    )
    parser.add_argument(
        "--body",
        required=True,
        help="The body of the pull request comment.",
    )

  def Run(self, args):
    pull_request_ref = args.CONCEPTS.pull_request.Parse()
    client = pull_request_comments.PullRequestCommentsClient(
        location=pull_request_ref.locationsId
    )

    create_operation = client.Create(
        pull_request_ref,
        args.body,
    )

    if args.async_:
      return create_operation

    # TODO(b/413742800): Remove the non wait logic once the LRO implemented.
    if create_operation.done:
      if create_operation.response:
        response_dict = encoding.MessageToPyValue(create_operation.response)
        comment_name = response_dict.get("name")
        if comment_name:
          log.CreatedResource(comment_name)
          return create_operation.response
      elif create_operation.error:
        log.error("Operation failed: " + str(create_operation.error))
      return create_operation

    operation_ref = resources.REGISTRY.ParseRelativeName(
        create_operation.name,
        collection="securesourcemanager.projects.locations.operations",
    )
    poller = waiter.CloudOperationPoller(
        client.client.projects_locations_repositories_pullRequests_pullRequestComments,
        client.client.projects_locations_operations,
    )
    response = waiter.WaitFor(
        poller, operation_ref, "Waiting for pull request comment to be created"
    )

    if response:
      response_dict = encoding.MessageToPyValue(response)
      comment_name = response_dict.get("name")
      if comment_name:
        log.CreatedResource(comment_name)

    return response


Create.detailed_help = DETAILED_HELP
