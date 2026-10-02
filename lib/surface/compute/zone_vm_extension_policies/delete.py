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

"""Command for deleting ZoneVmExtensionPolicies."""

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.zone_vm_extension_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.vm_extension_policies import flags as vm_extension_policies_flags
from googlecloudsdk.command_lib.compute.zone_vm_extension_policies import flags


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a Compute Engine zone VM extension policy."""

  detailed_help = {
      'brief': 'Delete a Compute Engine zone VM extension policy.',
      'EXAMPLES': """
     To delete a zone VM extension policy, run:

       $ {command} test-policy-name
   """,
  }

  ZONE_VM_EXTENSION_POLICIES_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ZONE_VM_EXTENSION_POLICIES_ARG = flags.MakeZoneVmExtensionPolicyArg()
    cls.ZONE_VM_EXTENSION_POLICIES_ARG.AddArgument(
        parser, operation_type='delete'
    )

  def Run(self, args):
    r"""Run the Delete command.

    Args:
      args: argparse.Namespace, The arguments to this command.

    Returns:
      Response calling the ZoneVmExtensionPoliciesService.Delete API.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    resource_ref = flags.ResolveZoneVmExtensionPolicyResource(
        args,
        holder,
        self.ZONE_VM_EXTENSION_POLICIES_ARG,
    )
    policy_client = client.ZoneVmExtensionPolicy.FromRef(
        resource_ref, holder.client
    )
    return policy_client.Delete()


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeleteAlpha(Delete):
  """Delete a Compute Engine zone VM extension policy."""

  @classmethod
  def Args(cls, parser):
    super(DeleteAlpha, cls).Args(parser)
    vm_extension_policies_flags.AddScopeFlags(parser)
