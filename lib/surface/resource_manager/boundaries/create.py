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
"""Command to create a boundary."""

from googlecloudsdk.api_lib.resource_manager import boundaries
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import operations
from googlecloudsdk.command_lib.resource_manager.boundaries import flags
from googlecloudsdk.command_lib.resource_manager.boundaries import resource_args
from googlecloudsdk.core import log


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Create(base.CreateCommand):
  r"""Create a new boundary.

  `{command}` creates a new boundary under the specified organization or folder.

  ## EXAMPLES

  To create a boundary with ID `my-boundary` in an organization with ID
  `123456789012`, run:

    $ {command} my-boundary \
        --organization=123456789012 \
        --display-name="My Boundary"

  To create a boundary with ID `my-boundary` in an organization with ID
  `123456789012` with a tag filter, run:

    $ {command} my-boundary \
        --organization=123456789012 \
        --display-name="My Boundary" \
        --tag-key=123456789012/env \
        --tag-value=production

  To create a boundary with ID `my-boundary` in a folder with ID `456789012345`,
  run:

    $ {command} my-boundary \
        --folder=456789012345 \
        --display-name="My Boundary" \
        --tag-key=123456789012/env \
        --tag-value=production
  """

  @staticmethod
  def Args(parser):
    resource_args.AddBoundaryResourceArgToParser(parser, 'to create')
    flags.AddDisplayNameArgToParser(parser, required=False)
    flags.AddTagKeyArgToParser(parser, required=False)
    flags.AddTagValueArgToParser(parser, required=False)
    flags.AddAsyncFlagToParser(parser)

  def Run(self, args):
    resource_ref = resource_args.ParseBoundary(args)
    parent = resource_ref.Parent().RelativeName()
    boundary_id = resource_ref.Name()
    op = boundaries.CreateBoundary(
        parent=parent,
        boundary_id=boundary_id,
        tag_key=args.tag_key,
        tag_value=args.tag_value,
        display_name=args.display_name,
    )
    if args.async_:
      return op

    result = operations.WaitForOperation(
        op,
        f'Waiting for Boundary [{boundary_id}] to be created',
        boundaries.GetBoundariesService(parent),
    )
    log.CreatedResource(result.name, kind='boundary')
    return result
