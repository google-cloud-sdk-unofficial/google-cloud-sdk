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
"""Command to update a boundary configuration."""

from typing import Any

from googlecloudsdk.api_lib.resource_manager import boundary_configs
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.resource_manager import boundary_configs_flags as flags
from googlecloudsdk.core import log


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Update(base.UpdateCommand):
  """Update a boundary configuration.

  `{command}` updates the boundary configuration under the specified
  organization or folder.

  ## EXAMPLES

  To update the tag key of the boundary configuration in an organization with
  ID `123456789012`, run:

    $ {command} --organization=123456789012 --tag-key=123456789012/env

  To update the tag key of the boundary configuration in a folder with ID
  `456789012345`, run:

    $ {command} --folder=456789012345 --tag-key=123456789012/env

  To clear the tag key of the boundary configuration in a folder with ID
  `456789012345`, run:

    $ {command} --folder=456789012345 --clear-tag-key
  """

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    flags.AddParentFlagsToParser(parser)
    flags.AddTagKeyFlagsToParser(parser)
    flags.AddEtagArgToParser(parser)
    flags.AddAsyncFlagToParser(parser)

  def Run(self, args: parser_extensions.Namespace) -> Any:
    name = flags.GetBoundaryConfigResourceName(args)
    tag_key = '' if args.clear_tag_key else args.tag_key
    operation = boundary_configs.UpdateBoundaryConfig(
        name=name,
        tag_key=tag_key,
        etag=args.etag,
    )
    if args.async_:
      if operation.done and operation.error:
        raise waiter.OperationError(operation.error.message)
      log.UpdatedResource(
          name, kind='boundaryConfig', is_async=not operation.done
      )
      return operation

    result = boundary_configs.WaitForOperation(
        operation,
        message=f'Waiting for BoundaryConfig [{name}] to be updated',
    )
    log.UpdatedResource(name, kind='boundaryConfig')
    return result
