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
"""Update command for the Resource Manager - CapabilityConfigs CLI."""

from googlecloudsdk.api_lib.resource_manager import capability_configs
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.resource_manager.capability_configs import flags
from googlecloudsdk.command_lib.resource_manager.capability_configs import resource_args
from googlecloudsdk.command_lib.resource_manager.capability_configs import util


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Update(base.UpdateCommand):
  r"""Update a CapabilityConfig.

  Updates the display name, types, or boundaries of an existing
  CapabilityConfig.

  ## EXAMPLES

  To update the display name of a CapabilityConfig:

        $ {command} my-config --folder=123456789 --display-name="Updated Config
        Name"

  To update the associated boundaries:

        $ {command} my-config --organization=123456789
        --boundaries=organizations/123456789/boundaries/b1,organizations/123456789/boundaries/b2

  To clear all boundaries associated with a CapabilityConfig:

        $ {command} my-config --organization=123456789 --clear-boundaries
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCapabilityConfigResourceArgToParser(
        parser, 'to update', positional=True, required=True
    )
    flags.AddDisplayNameArgToParser(parser)
    flags.AddTypesArgToParser(parser, required=False)
    boundaries_group = parser.add_mutually_exclusive_group()
    flags.AddBoundariesArgToParser(boundaries_group)
    flags.AddClearBoundariesArgToParser(boundaries_group)
    flags.AddEtagArgToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    messages = capability_configs.CapabilityConfigsMessages()
    resource_ref = resource_args.ParseCapabilityConfig(args)
    name = resource_ref.RelativeName()
    update_mask = util.GetUpdateMask(args)

    if not update_mask:
      raise calliope_exceptions.MinimumArgumentException(
          ['--display-name', '--types', '--boundaries', '--clear-boundaries'],
          'Please specify at least one property to update.',
      )

    config = messages.CapabilityConfig(name=name)
    if args.IsSpecified('display_name'):
      config.displayName = args.display_name
    if args.IsSpecified('types'):
      config.types = util.ParseTypes(args.types, messages)
    if args.IsSpecified('boundaries'):
      config.boundaries = args.boundaries
    elif args.IsSpecified('clear_boundaries'):
      config.boundaries = []
    if args.IsSpecified('etag'):
      config.etag = args.etag

    op = capability_configs.Update(name, config, update_mask)

    if args.async_:
      return op

    return capability_configs.WaitForOperation(
        op,
        message=f'Waiting for CapabilityConfig [{name}] to be updated',
    )
