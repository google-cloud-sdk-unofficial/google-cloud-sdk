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
"""Delete command for Resource Manager Semantic Tag Bindings."""

from googlecloudsdk.api_lib.resource_manager import semantic_tags
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import endpoint_utils as endpoints
from googlecloudsdk.command_lib.resource_manager import operations
from googlecloudsdk.command_lib.resource_manager.semantic_tags import flags
from googlecloudsdk.command_lib.resource_manager.semantic_tags import utils
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  r"""Delete a Semantic Tag Binding.

  `{command}` deletes a Semantic Tag Binding by its full resource name or
  binding ID.

  ## EXAMPLES

  To delete a Semantic Tag Binding by its full resource name, run:

    $ {command} \
        projects/acme-sec-prod/locations/us-central1/semanticTagBindings/stb-bk3v7q2m6x4t5p2c6r5n7w

  To delete a Semantic Tag Binding by its short ID under `organizations/1001`
  in `us-central1`, run:

    $ {command} stb-bk3v7q2m6x4t5p2c6r5n7w \
        --parent=organizations/1001 --location=us-central1
  """

  @staticmethod
  def Args(parser):
    flags.AddBindingNameArgToParser(
        parser,
        help_text=(
            'Resource name or short ID of the Semantic Tag Binding to delete.'
        ),
    )
    flags.AddLocationArgToParser(parser, required=False, default='global')
    flags.AddBindingParentArgToParser(parser)
    flags.AddValidateOnlyArgToParser(parser, action_description='delete')
    flags.AddAsyncArgToParser(parser)

  def Run(self, args):
    full_name, _, location, _ = utils.ParseSemanticTagBindingName(args)

    if not args.validate_only:
      console_io.PromptContinue(
          message=(
              f'You are about to delete Semantic Tag Binding [{full_name}].'
          ),
          cancel_on_no=True,
      )

    with endpoints.CrmEndpointOverrides(location):
      op = semantic_tags.DeleteSemanticTagBinding(
          name=full_name,
          validate_only=args.validate_only,
      )
      if args.validate_only:
        log.status.Print('Request is valid. No resources were deleted.')
        return op
      if args.async_:
        log.DeletedResource(
            full_name, kind='Semantic Tag Binding', is_async=True
        )
        return op

      result = operations.WaitForReturnOperation(
          op,
          f'Waiting for Semantic Tag Binding [{full_name}] to be deleted',
      )
      log.DeletedResource(full_name, kind='Semantic Tag Binding')
      return result
