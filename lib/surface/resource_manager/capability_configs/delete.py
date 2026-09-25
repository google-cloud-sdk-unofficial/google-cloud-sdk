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
"""Delete command for the Resource Manager - CapabilityConfigs CLI."""

from googlecloudsdk.api_lib.resource_manager import capability_configs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager.capability_configs import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Delete(base.DeleteCommand):
  r"""Delete a CapabilityConfig.

  Deletes an existing CapabilityConfig given its ID and parent or its
  fully-qualified resource name.

  ## EXAMPLES

  To delete a CapabilityConfig `my-config` under folder `123456789`:

        $ {command} my-config --folder=123456789

  To delete a CapabilityConfig by its full resource name:

        $ {command} organizations/123456789/capabilityConfigs/my-config
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCapabilityConfigResourceArgToParser(
        parser, 'to delete', positional=True, required=True
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    resource_ref = resource_args.ParseCapabilityConfig(args)
    name = resource_ref.RelativeName()

    console_io.PromptContinue(
        f'You are about to delete CapabilityConfig [{name}]',
        throw_if_unattended=True,
        cancel_on_no=True,
    )

    op = capability_configs.Delete(name)

    if args.async_:
      return op

    result = capability_configs.WaitForOperation(
        op,
        message=f'Waiting for CapabilityConfig [{name}] to be deleted',
        has_result=False,
    )
    log.DeletedResource(name, kind='capability config')
    return result
