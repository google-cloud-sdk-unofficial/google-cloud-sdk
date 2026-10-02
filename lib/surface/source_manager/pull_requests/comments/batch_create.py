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
"""Batch create Secure Source Manager pull request comments command."""

from googlecloudsdk.api_lib.securesourcemanager import pull_request_comments
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.source_manager import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

DETAILED_HELP = {
    "DESCRIPTION": (
        """
          Batch create comments for a Secure Source Manager pull request.
        """
    ),
    "EXAMPLES": (
        """
            To batch create comments in pull request `1` of repository `my-repo` and location `us-central1` using comments defined in `comments.yaml`, run the following command:

            $ {command} --pull-request=1 --repository=my-repo --region=us-central1 --comments-file=comments.yaml
        """
    ),
}


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.RegionalEndpointsSupported
class BatchCreate(base.CreateCommand):
  """Batch create Secure Source Manager pull request comments."""

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    resource_args.AddPullRequestResourceArgAsFlag(
        parser, "to batch create comments under"
    )
    parser.add_argument(
        "--comments-file",
        required=True,
        help=(
            "Path to a YAML or JSON file containing a list of pull request"
            " comments to create."
        ),
    )

  def Run(self, args):
    pull_request_ref = args.CONCEPTS.pull_request.Parse()
    client = pull_request_comments.PullRequestCommentsClient(
        location=pull_request_ref.locationsId
    )
    try:
      content = files.ReadFileContents(args.comments_file)
    except files.Error as e:
      raise exceptions.InvalidArgumentException(
          "--comments-file", "Failed to read file: {}".format(e)
      )

    try:
      comments_list = yaml.load(content)
    except yaml.YAMLParseError as e:
      raise exceptions.InvalidArgumentException(
          "--comments-file", "Failed to parse YAML/JSON from file: {}".format(e)
      )

    if not isinstance(comments_list, list):
      raise exceptions.InvalidArgumentException(
          "--comments-file",
          "The comments file must contain a list of comments.",
      )

    create_operation = client.BatchCreate(pull_request_ref, comments_list)

    if args.async_:
      return create_operation

    # TODO(b/413742800): Remove the non wait logic once the LRO implemented.
    if create_operation.done or not create_operation.name:
      if create_operation.error:
        raise waiter.OperationError(
            create_operation.error.message or str(create_operation.error)
        )
      log.status.Print(
          "Batch create comments request completed for [{}].".format(
              pull_request_ref.RelativeName()
          )
      )
      return create_operation

    response = client.WaitForOperation(
        client.GetOperationRef(create_operation),
        "Waiting for pull request comments to be created",
        has_result=False,
    )
    log.status.Print(
        "Batch create comments request completed for [{}].".format(
            pull_request_ref.RelativeName()
        )
    )
    return response


BatchCreate.detailed_help = DETAILED_HELP
