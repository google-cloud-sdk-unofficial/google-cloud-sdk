# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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

"""Command for listing GlobalVmExtensionPolicies."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.global_vm_extension_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.vm_extension_policies import flags as vm_extension_policies_flags


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Compute Engine global VM extension policies."""

  detailed_help = {
      'brief': 'List Compute Engine global VM extension policies.',
      'EXAMPLES': """
     To list all global VM extension policy, run:

       $ {command}
   """,
  }

  def Run(self, args):
    r"""Run the List command.

    Args:
      args: argparse.Namespace, The arguments to this command.

    Returns:
      Response calling the GlobalVmExtensionPoliciesService.List API.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    policy_client = client.GlobalVmExtensionPolicy.FromArgs(args, holder.client)
    return policy_client.List()


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(List):
  """List Compute Engine global VM extension policies."""

  @classmethod
  def Args(cls, parser):
    super(ListAlpha, cls).Args(parser)
    vm_extension_policies_flags.AddScopeFlags(parser)
