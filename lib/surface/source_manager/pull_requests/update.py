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
"""Update Secure Source Manager pull request command."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.securesourcemanager import pull_requests
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.source_manager import flags
from googlecloudsdk.command_lib.source_manager import resource_args
from googlecloudsdk.core import log

DETAILED_HELP = {
    "DESCRIPTION": (
        """
          Update a Secure Source Manager pull request.
        """
    ),
    "EXAMPLES": (
        """
            To update the title of a pull request 1 in repository 'my-repo' in location 'us-central1', run the following command:

            $ {command} 1 --repository=my-repo --region=us-central1 --title='Updated Title'
        """
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.RegionalEndpointsSupported
class Update(base.UpdateCommand):
  """Update a Secure Source Manager pull request."""

  NO_CHANGES_MESSAGE = (
      "There are no changes to the pull request [{pull_request}] for update"
  )

  @staticmethod
  def Args(parser):
    resource_args.AddPullRequestResourceArg(parser, "to update")
    flags.AddTitle(parser, required=False)
    flags.AddBody(parser, required=False)

  def Run(self, args):
    pull_request_ref = args.CONCEPTS.pull_request.Parse()
    client = pull_requests.PullRequestsClient(
        location=pull_request_ref.locationsId
    )

    update_mask = []
    if args.IsSpecified("title"):
      update_mask.append("title")
    if args.IsSpecified("body"):
      update_mask.append("body")

    if not update_mask:
      raise exceptions.MinimumArgumentException(
          [
              "--title",
              "--body",
          ],
          self.NO_CHANGES_MESSAGE.format(pull_request=pull_request_ref.Name()),
      )

    update_operation = client.Update(
        pull_request_ref,
        title=args.title,
        body=args.body,
        update_mask=update_mask,
    )

    # Log the updated pull request name if the operation is successful otherwise
    # log the error.
    if update_operation.done and update_operation.response:
      response_dict = encoding.MessageToPyValue(update_operation.response)
      pr_name = response_dict.get("name", pull_request_ref.RelativeName())
      if pr_name:
        log.UpdatedResource(pr_name)
    elif update_operation.error:
      log.error("Operation failed: " + str(update_operation.error))

    return update_operation


Update.detailed_help = DETAILED_HELP
