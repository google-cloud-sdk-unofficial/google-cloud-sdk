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
"""Update Secure Source Manager hook command."""

from googlecloudsdk.api_lib.securesourcemanager import hooks
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.source_manager import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis.securesourcemanager.v1 import securesourcemanager_v1_messages

DETAILED_HELP = {
    "DESCRIPTION": (
        """
          Update a Secure Source Manager hook.
        """
    ),
    "EXAMPLES": (
        """
            To disable a hook ``my-hook'' in repository ``my-repo'' and location ``us-central1'', run the following command:

            $ {command} my-hook --repository=my-repo --region=us-central1 --disabled

            To enable the same hook, run:

            $ {command} my-hook --repository=my-repo --region=us-central1 --no-disabled
        """
    ),
}


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
@base.RegionalEndpointsSupported
class Update(base.UpdateCommand):
  """Update a Secure Source Manager hook."""

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    base.ASYNC_FLAG.AddToParser(parser)
    resource_args.AddHookResourceArg(parser, "to update")
    parser.add_argument(
        "--target-uri",
        required=False,
        help="The target URI to which the payloads will be delivered.",
    )
    parser.add_argument(
        "--events",
        metavar="EVENT",
        type=arg_parsers.ArgList(),
        required=False,
        help=(
            "The events that trigger hook on. Can be PUSH, PULL_REQUEST, or"
            " PULL_REQUEST_COMMENT."
        ),
    )
    parser.add_argument(
        "--disabled",
        action=arg_parsers.StoreTrueFalseAction,
        required=False,
        inverted_help_text=True,
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

    update_mask = []
    if args.IsSpecified("target_uri"):
      update_mask.append("target_uri")
    if args.IsSpecified("events"):
      update_mask.append("events")
    if args.IsSpecified("disabled"):
      update_mask.append("disabled")

    if not update_mask:
      raise exceptions.MinimumArgumentException(
          [
              "--target-uri",
              "--events",
              "--disabled",
          ],
          "At least one argument is required.",
      )

    update_operation = client.Update(
        hook_ref,
        target_uri=args.target_uri,
        events=args.events,
        disabled=args.disabled,
        update_mask=update_mask,
    )

    if args.async_:
      log.UpdatedResource(hook_ref.RelativeName(), is_async=True)
      return update_operation

    response = client.GetOperationResult(
        update_operation, "Waiting for hook to be updated"
    )
    log.UpdatedResource(hook_ref.RelativeName())
    return response


Update.detailed_help = DETAILED_HELP
