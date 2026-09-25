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
"""Merge Secure Source Manager pull request command."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.securesourcemanager import pull_requests
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.source_manager import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

DETAILED_HELP = {
    "DESCRIPTION": (
        """
          Merge a Secure Source Manager pull request.
        """
    ),
    "EXAMPLES": (
        """
            To merge a pull request 1 in repository `my-repo` and location `us-central1`, run the following command:

            $ {command} 1 --repository=my-repo --region=us-central1
        """
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
@base.RegionalEndpointsSupported
class Merge(base.Command):
  """Merge a Secure Source Manager pull request."""

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    resource_args.AddPullRequestResourceArg(parser, "to merge")

  def Run(self, args):
    pull_request_ref = args.CONCEPTS.pull_request.Parse()
    client = pull_requests.PullRequestsClient(
        location=pull_request_ref.locationsId
    )
    merge_operation = client.Merge(pull_request_ref)

    if args.async_:
      return merge_operation

    # TODO(b/413742800): Remove the non wait logic once the LRO implemented.
    if merge_operation.done:
      if merge_operation.response:
        response_dict = encoding.MessageToPyValue(merge_operation.response)
        pr_name = response_dict.get("name")
        if pr_name:
          log.status.Print("Merge request issued for [{}].".format(pr_name))
          return merge_operation.response
      elif merge_operation.error:
        log.error("Operation failed: " + str(merge_operation.error))
      else:
        log.status.Print(
            "Merge request issued for [{}].".format(
                pull_request_ref.RelativeName()
            )
        )
      return merge_operation

    operation_ref = resources.REGISTRY.ParseRelativeName(
        merge_operation.name,
        collection="securesourcemanager.projects.locations.operations",
    )
    poller = waiter.CloudOperationPoller(
        client.client.projects_locations_repositories_pullRequests,
        client.client.projects_locations_operations,
    )
    response = waiter.WaitFor(
        poller, operation_ref, "Waiting for pull request to be merged"
    )

    if response:
      response_dict = encoding.MessageToPyValue(response)
      pr_name = response_dict.get("name", pull_request_ref.RelativeName())
      if pr_name:
        log.status.Print("Merge request issued for [{}].".format(pr_name))

    return response


Merge.detailed_help = DETAILED_HELP
