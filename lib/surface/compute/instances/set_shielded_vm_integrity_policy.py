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
"""Command for setting Shielded VM integrity policy for VM instances."""


from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags

_DETAILED_HELP = {
    'brief': 'Set the Shielded VM integrity policy for a VM instance.',
    'DESCRIPTION': (
        """\
        Updates the integrity policy baseline using the measurements from
        the VM instance's most recent boot. You can only use this method on
        a running VM instance.
        """
    ),
    'EXAMPLES': (
        """\
        To update the auto-learn policy for an instance named 'my-instance',
        run:

            $ {command} my-instance --update-auto-learn-policy
        """
    ),
}


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class SetShieldedVmIntegrityPolicy(base.SilentCommand):
  """Sets the Shielded VM integrity policy for a VM instance."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser)
    parser.add_argument(
        '--update-auto-learn-policy',
        action=arg_parsers.StoreTrueFalseAction,
        required=True,
        help=("""\
            Specifies whether to update the auto-learn policy for the VM
            instance.
            """),
    )

  def Run(self, args):
    errors = []

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client),
    )
    shielded_vm_integrity_policy = messages.ShieldedVmIntegrityPolicy(
        updateAutoLearnPolicy=args.update_auto_learn_policy
    )

    request = (
        client.apitools_client.instances,
        'SetShieldedVmIntegrityPolicy',
        messages.ComputeInstancesSetShieldedVmIntegrityPolicyRequest(
            instance=instance_ref.instance,
            zone=instance_ref.zone,
            project=instance_ref.project,
            shieldedVmIntegrityPolicy=shielded_vm_integrity_policy,
        ),
    )

    response = client.MakeRequests(requests=[request], errors_to_collect=errors)
    if errors:
      utils.RaiseToolException(
          errors,
          error_message=(
              'Failed to set Shielded VM integrity policy for an instance.'
          ),
      )

    return response[0]
