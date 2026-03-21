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

"""Command for listing vm extensions available in a zone."""

import argparse
import textwrap
from typing import Any as typing_Any, List as typing_List

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.zone_vm_extension_policies import extensions_flags as flags
from googlecloudsdk.core import properties


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Vm Extensions in a zone."""

  detailed_help = {
      'brief': 'List Vm Extensions in a zone.',
      'EXAMPLES': textwrap.dedent("""
     To list all Vm Extensions in a zone, run:

       $ {command} --zone=<zone>
   """),
  }

  @classmethod
  def Args(cls, parser: argparse.ArgumentParser) -> None:
    cls.ZoneVmExtensionPoliciesArg = flags.AddZoneFlag(parser)

  def Run(self, args: argparse.Namespace) -> typing_List[typing_Any]:
    r"""Run the List command.

    Args:
      args: argparse.Namespace, The arguments to this command.

    Returns:
      Response calling the ZoneVmExtensionPoliciesService.ListVmExtensions API.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = holder.client.messages
    return client.MakeRequests([(
        client.apitools_client.zoneVmExtensionPolicies,
        'ListVmExtensions',
        messages.ComputeZoneVmExtensionPoliciesListVmExtensionsRequest(
            project=properties.VALUES.core.project.GetOrFail(),
            zone=args.zone
        ),
    )])
