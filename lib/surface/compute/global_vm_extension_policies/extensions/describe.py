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

"""Command for getting info for a global VM extension."""

import argparse
import textwrap
from typing import Any, List

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.global_vm_extension_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.global_vm_extension_policies import extensions_flags as flags


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe a vm extension at the global level."""

  detailed_help = {
      'brief': 'Describe a vm extension at the global level.',
      'EXAMPLES': textwrap.dedent("""
     To describe a vm extension at the global level, run:

       $ {command} extension-name
   """),
  }

  GLOBAL_VM_EXTENSION_POLICIES_ARG = None

  @classmethod
  def Args(cls, parser: argparse.ArgumentParser) -> None:
    cls.GLOBAL_VM_EXTENSION_POLICIES_ARG = (
        flags.MakeGlobalVmExtensionPolicyArg()
    )
    cls.GLOBAL_VM_EXTENSION_POLICIES_ARG.AddArgument(
        parser, operation_type='describe'
    )
    flags.AddScopeFlags(parser)

  def Run(
      self, args: argparse.Namespace
  ) -> List[Any]:
    r"""Run the Describe command.

    Args:
      args: argparse.Namespace, The arguments to this command.

    Returns:
      Response calling the GlobalVmExtensionPoliciesService.GetVmExtension API.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    resource_ref = flags.ResolveGlobalVmExtensionPolicyResource(
        args,
        holder,
        self.GLOBAL_VM_EXTENSION_POLICIES_ARG,
    )
    policy_client = client.GlobalVmExtensionPolicy.FromRef(
        resource_ref, holder.client
    )
    return policy_client.DescribeExtension()
