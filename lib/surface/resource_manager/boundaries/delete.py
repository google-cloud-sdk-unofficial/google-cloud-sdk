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
"""Command to delete a boundary."""

from googlecloudsdk.api_lib.resource_manager import boundaries
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import operations
from googlecloudsdk.command_lib.resource_manager.boundaries import flags
from googlecloudsdk.command_lib.resource_manager.boundaries import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Delete(base.DeleteCommand):
  """Delete a boundary.

  `{command}` deletes an existing boundary given its ID and parent or its full
  resource name.

  ## EXAMPLES

  To delete a boundary with ID `my-boundary` in an organization with ID
  `123456789012`, run:

    $ {command} my-boundary --organization=123456789012

  To delete a boundary by full resource name, run:

    $ {command} organizations/123456789012/boundaries/my-boundary
  """

  @staticmethod
  def Args(parser):
    resource_args.AddBoundaryResourceArgToParser(parser, 'to delete')
    flags.AddAsyncFlagToParser(parser)

  def Run(self, args):
    resource_ref = resource_args.ParseBoundary(args)
    name = resource_ref.RelativeName()
    if not console_io.PromptContinue(
        message=f'You are about to delete boundary [{name}].',
        cancel_on_no=True,
    ):
      return None

    op = boundaries.DeleteBoundary(boundary_name=name)
    if args.async_:
      return op

    result = operations.WaitForReturnOperation(
        op, f'Waiting for Boundary [{name}] to be deleted'
    )
    log.DeletedResource(name, kind='boundary')
    return result
