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
"""Create Secure Source Manager pull request command."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.securesourcemanager import pull_requests
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.source_manager import flags
from googlecloudsdk.command_lib.source_manager import resource_args
from googlecloudsdk.core import log

DETAILED_HELP = {
    "DESCRIPTION": (
        """
          Create a Secure Source Manager pull request.
        """
    ),
    "EXAMPLES": (
        """
            To create a pull request in a repository called 'my-repo' in location 'us-central1', run the following command:

            $ {command} --repository=my-repo --region=us-central1 --title="My pull request" --body="My pull request description" --base-branch="main" --head-branch="new-branch"
        """
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.RegionalEndpointsSupported
class Create(base.CreateCommand):
  """Create a Secure Source Manager pull request."""

  @staticmethod
  def Args(parser):
    resource_args.AddRepositoryResourceArgAsFlag(
        parser, "to create pull request in"
    )
    flags.AddTitle(parser)
    flags.AddBody(parser)
    flags.AddBaseBranch(parser)
    flags.AddHeadBranch(parser)

  def Run(self, args):
    repository_ref = args.CONCEPTS.repository.Parse()
    client = pull_requests.PullRequestsClient(
        location=repository_ref.locationsId
    )

    create_operation = client.Create(
        repository_ref,
        args.title,
        args.body,
        args.base_branch,
        args.head_branch,
    )

    # Log the created pull request name if the operation is successful otherwise
    # log the error.
    if create_operation.done and create_operation.response:
      response_dict = encoding.MessageToPyValue(create_operation.response)
      pr_name = response_dict.get("name")
      if pr_name:
        log.CreatedResource(pr_name)
    elif create_operation.error:
      log.error("Operation failed: " + str(create_operation.error))

    return create_operation


Create.detailed_help = DETAILED_HELP
