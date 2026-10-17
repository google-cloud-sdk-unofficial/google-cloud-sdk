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
"""Create Secure Source Manager issue command."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.securesourcemanager import issues
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.source_manager import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis.securesourcemanager.v1 import securesourcemanager_v1_messages

DETAILED_HELP = {
    "DESCRIPTION": (
        """
          Create a Secure Source Manager issue.
        """
    ),
    "EXAMPLES": (
        """
            To create an issue in repository ``my-repo'' in location ``us-central1'' with title ``My Issue'' and body ``Details'', run the following command:

            $ {command} --repository=my-repo --region=us-central1 --title='My Issue' --body='Details'
        """
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
@base.RegionalEndpointsSupported
class Create(base.CreateCommand):
  """Create a Secure Source Manager issue."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.ASYNC_FLAG.AddToParser(parser)
    resource_args.AddRepositoryResourceArgAsFlag(parser, "to create issue in")
    parser.add_argument(
        "--title",
        required=True,
        help="The title of the issue.",
    )
    parser.add_argument(
        "--body",
        required=False,
        help="The body of the issue.",
    )

  def Run(
      self, args: parser_extensions.Namespace
  ) -> (
      securesourcemanager_v1_messages.Operation
      | securesourcemanager_v1_messages.Operation.ResponseValue
      | securesourcemanager_v1_messages.Issue
      | None
  ):
    repository_ref = args.CONCEPTS.repository.Parse()
    client = issues.IssuesClient(location=repository_ref.locationsId)

    create_operation = client.Create(
        repository_ref,
        args.title,
        args.body,
    )

    if args.async_:
      return create_operation

    # TODO(b/413742800): Remove the non wait logic once the LRO implemented.
    if create_operation.done or not create_operation.name:
      if create_operation.error:
        raise waiter.OperationError(
            create_operation.error.message or str(create_operation.error)
        )
      if create_operation.response:
        response_dict = encoding.MessageToPyValue(create_operation.response)
        issue_name = response_dict.get("name")
        if issue_name:
          log.CreatedResource(issue_name)
      return create_operation.response

    response = client.WaitForOperation(
        client.GetOperationRef(create_operation),
        "Waiting for issue to be created",
    )
    if response:
      response_dict = encoding.MessageToPyValue(response)
      issue_name = response_dict.get("name")
      if issue_name:
        log.CreatedResource(issue_name)

    return response


Create.detailed_help = DETAILED_HELP
