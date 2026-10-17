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
"""Create Secure Source Manager hook command."""

from googlecloudsdk.api_lib.securesourcemanager import hooks
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
          Create a Secure Source Manager hook.
        """
    ),
    "EXAMPLES": (
        """
            To create a hook ``my-hook'' in repository ``my-repo'' in location ``us-central1'' targeting ``https://example.com/webhook'', run the following command:

            $ {command} my-hook --repository=my-repo --region=us-central1 --target-uri=https://example.com/webhook --events=PUSH,PULL_REQUEST
        """
    ),
}

# Choices for webhooks events. Please update if new events are added.
_EVENT_CHOICES = {
    "PUSH": "Push events are triggered when pushing to the repository.",
    "PULL_REQUEST": (
        "Pull request events are triggered when a pull request is opened,"
        " closed, reopened, or edited."
    ),
    "PULL_REQUEST_COMMENT": (
        "Triggers when a general comment is added, edited, or deleted on a"
        " pull request."
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
@base.RegionalEndpointsSupported
class Create(base.CreateCommand):
  """Create a Secure Source Manager hook."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.ASYNC_FLAG.AddToParser(parser)
    resource_args.AddHookResourceArg(parser, "to create")
    parser.add_argument(
        "--target-uri",
        required=True,
        help="The target URI to which the payloads will be delivered.",
    )
    parser.add_argument(
        "--events",
        metavar="EVENT",
        type=arg_parsers.ArgList(choices=_EVENT_CHOICES),
        required=False,
        default=[],
        help=(
            "The events that trigger hook on. Can be PUSH, PULL_REQUEST, or"
            " PULL_REQUEST_COMMENT."
        ),
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        required=False,
        default=False,
        help="Determines if the hook is disabled.",
    )

  def Run(
      self, args: parser_extensions.Namespace
  ) -> (
      securesourcemanager_v1_messages.Operation
      | securesourcemanager_v1_messages.Operation.ResponseValue
      | securesourcemanager_v1_messages.Hook
      | None
  ):
    hook_ref = args.CONCEPTS.hook.Parse()
    client = hooks.HooksClient(location=hook_ref.locationsId)

    create_operation = client.Create(
        hook_ref,
        args.target_uri,
        args.events,
        args.disabled,
    )

    if args.async_:
      log.CreatedResource(hook_ref.RelativeName(), is_async=True)
      return create_operation

    response = client.GetOperationResult(
        create_operation, "Waiting for hook to be created"
    )
    log.CreatedResource(hook_ref.RelativeName())
    return response


Create.detailed_help = DETAILED_HELP
