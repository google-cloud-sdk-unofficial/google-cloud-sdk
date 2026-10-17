# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Command for resetting an instance."""


from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags

DETAILED_HELP = {
    'brief': 'Reset a virtual machine instance.',
    'DESCRIPTION':
        """\
          *{command}* is used to perform a hard reset on a
        Compute Engine virtual machine.

        This will not perform a clean shutdown of the guest OS on the instance.
        """,
    'EXAMPLES':
        """\
        To reset an instance named ``test-instance'', run:

          $ {command} test-instance
        """
}

DETAILED_HELP_PREVIEW = {
    'brief': 'Reset a virtual machine instance.',
    'DESCRIPTION':
        """\
          *{command}* is used to reset a Compute Engine virtual machine.

        By default, this performs a hard reset, which does not perform a clean
        shutdown of the guest OS on the instance. Use `--reset-mode` to select
        a different reset mode.
        """,
    'EXAMPLES':
        """\
        To reset an instance named ``test-instance'', run:

          $ {command} test-instance

        To send a graceful reset to the guest OS of an instance named
        ``test-instance'', run:

          $ {command} test-instance --reset-mode=soft-reset

        To power cycle an instance named ``test-instance'', run:

          $ {command} test-instance --reset-mode=power-cycle
        """
}

# Maps --reset-mode flag choices to their help text. Each choice corresponds to
# a ResetModeValueValuesEnum value (upper-cased, with '-' replaced by '_').
_RESET_MODE_CHOICES = {
    'hard-reset': (
        'Performs a hard reset on the instance. This immediately restarts the'
        ' instance without gracefully shutting down the guest operating'
        ' system. This is the default.'
    ),
    'soft-reset': (
        'Sends a graceful reset command to the guest operating system (e.g.,'
        ' equivalent to running `sudo reboot`).'
    ),
    'power-cycle': 'Performs a machine-level power cycle.',
}


@base.UniverseCompatible
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.GA,
)
class Reset(base.SilentCommand):
  """Reset a virtual machine instance."""

  @staticmethod
  def Args(parser):
    flags.INSTANCES_ARG.AddArgument(parser)

  def _CreateResetRequest(self, client, instance_ref, args):
    del args  # Unused.
    return client.messages.ComputeInstancesResetRequest(
        instance=instance_ref.Name(),
        project=instance_ref.project,
        zone=instance_ref.zone)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_refs = flags.INSTANCES_ARG.ResolveAsResource(
        args, holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client))
    request_list = []
    for instance_ref in instance_refs:
      request = self._CreateResetRequest(client, instance_ref, args)
      request_list.append((client.apitools_client.instances, 'Reset', request))
    return client.MakeRequests(request_list)


@base.ReleaseTracks(base.ReleaseTrack.PREVIEW)
@base.UniverseCompatible
class ResetPreview(Reset):
  """Reset a virtual machine instance."""

  @staticmethod
  def Args(parser):
    Reset.Args(parser)
    parser.add_argument(
        '--reset-mode',
        choices=_RESET_MODE_CHOICES,
        help='The mode of the reset operation.',
    )

  def _CreateResetRequest(self, client, instance_ref, args):
    request = super()._CreateResetRequest(client, instance_ref, args)
    if args.reset_mode:
      request.resetMode = (
          client.messages.ComputeInstancesResetRequest.ResetModeValueValuesEnum(
              args.reset_mode.replace('-', '_').upper()
          )
      )
    return request


Reset.detailed_help = DETAILED_HELP
ResetPreview.detailed_help = DETAILED_HELP_PREVIEW
