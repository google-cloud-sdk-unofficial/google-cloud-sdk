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
"""Command to update a boundary."""

from googlecloudsdk.api_lib.resource_manager import boundaries
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.resource_manager import operations
from googlecloudsdk.command_lib.resource_manager.boundaries import flags
from googlecloudsdk.command_lib.resource_manager.boundaries import resource_args
from googlecloudsdk.core import log


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Update(base.UpdateCommand):
  r"""Update a boundary.

  `{command}` updates the display name or tag value of an existing boundary.

  ## EXAMPLES

  To update a boundary with ID `my-boundary` in an organization with ID
  `123456789012`, run:

    $ {command} my-boundary \
        --organization=123456789012 \
        --display-name="Updated Name" \
        --tag-value=staging
  """

  @staticmethod
  def Args(parser):
    resource_args.AddBoundaryResourceArgToParser(parser, 'to update')
    flags.AddDisplayNameArgToParser(parser, required=False)
    flags.AddTagValueArgToParser(parser, required=False)
    flags.AddEtagArgToParser(parser)
    flags.AddAsyncFlagToParser(parser)

  def Run(self, args):
    if args.display_name is None and args.tag_value is None:
      raise calliope_exceptions.MinimumArgumentException(
          ['--display-name', '--tag-value']
      )
    resource_ref = resource_args.ParseBoundary(args)
    name = resource_ref.RelativeName()
    op = boundaries.UpdateBoundary(
        boundary_name=name,
        display_name=args.display_name,
        tag_value=args.tag_value,
        etag=args.etag,
    )
    if args.async_:
      return op

    result = operations.WaitForOperation(
        op,
        f'Waiting for Boundary [{name}] to be updated',
        boundaries.GetBoundariesService(name),
    )
    log.UpdatedResource(result.name, kind='boundary')
    return result
