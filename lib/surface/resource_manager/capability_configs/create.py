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
"""Create command for the Resource Manager - CapabilityConfigs CLI."""

from googlecloudsdk.api_lib.resource_manager import capability_configs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager.capability_configs import flags
from googlecloudsdk.command_lib.resource_manager.capability_configs import resource_args
from googlecloudsdk.command_lib.resource_manager.capability_configs import util


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Create(base.CreateCommand):
  r"""Create a CapabilityConfig under a parent Organization, Folder, or Project.

  Creating a CapabilityConfig triggers the creation of a Management Project if
  one is not supplied via `--management-project`.

  ## EXAMPLES

  To create a CapabilityConfig `my-config` with type `app-management` under
  organization `123456789`:

        $ {command} my-config --organization=123456789 --types=app-management

  To create a CapabilityConfig with display name and pre-existing management
  project:

        $ {command} my-config --folder=456789012 --types=app-management
        --display-name="App Hub Config"
        --management-project=projects/123456789012
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCapabilityConfigResourceArgToParser(
        parser, 'to create', positional=True, required=True
    )
    flags.AddTypesArgToParser(parser, required=True)
    flags.AddDisplayNameArgToParser(parser)
    flags.AddManagementProjectArgToParser(parser)
    flags.AddBoundariesArgToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    messages = capability_configs.CapabilityConfigsMessages()
    resource_ref = resource_args.ParseCapabilityConfig(args)
    parent = resource_ref.Parent().RelativeName()
    capability_config_id = resource_ref.Name()

    types = util.ParseTypes(args.types, messages)
    config = messages.CapabilityConfig(types=types)

    if args.IsSpecified('display_name'):
      config.displayName = args.display_name
    if args.IsSpecified('management_project'):
      config.managementProject = args.management_project
    if args.IsSpecified('boundaries'):
      config.boundaries = args.boundaries

    op = capability_configs.Create(parent, capability_config_id, config)

    if args.async_:
      return op

    return capability_configs.WaitForOperation(
        op,
        message=(
            f'Waiting for CapabilityConfig [{capability_config_id}] to be'
            ' created'
        ),
    )
