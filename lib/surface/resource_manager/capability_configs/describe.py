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
"""Describe command for the Resource Manager - CapabilityConfigs CLI."""

from googlecloudsdk.api_lib.resource_manager import capability_configs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager.capability_configs import resource_args


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Describe(base.DescribeCommand):
  r"""Describe a CapabilityConfig.

  Retrieves metadata for a CapabilityConfig given its ID and parent or its
  fully-qualified resource name.

  ## EXAMPLES

  To describe a CapabilityConfig `my-config` under folder `123456789`:

        $ {command} my-config --folder=123456789

  To describe a CapabilityConfig by its full resource name:

        $ {command} organizations/123456789/capabilityConfigs/my-config
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCapabilityConfigResourceArgToParser(
        parser, 'to describe', positional=True, required=True
    )

  def Run(self, args):
    resource_ref = resource_args.ParseCapabilityConfig(args)
    name = resource_ref.RelativeName()
    return capability_configs.Get(name)
