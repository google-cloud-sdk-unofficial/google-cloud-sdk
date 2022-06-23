# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command for troubleshooting problems with the VM Manager."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.command_lib.compute.os_config import troubleshooter
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Troubleshoot(base.Command):
  """Troubleshoot VM Manager issues.

  ## EXAMPLES

  The following command troubleshoots issues for a VM instance with the name
  `my-instance-name` in the zone `us-central1-a`:

    $ {command} my-instance-name --zone=us-central1-a

  """

  def _ResolveInstance(self, holder, compute_client, args):
    """Resolves the arguments into an instance.

    Args:
      holder: the api holder
      compute_client: the compute client
      args: The command line arguments.

    Returns:
      An instance reference to a VM.
    """
    resources = holder.resources
    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        resources,
        scope_lister=flags.GetInstanceZoneScopeLister(compute_client))
    return instance_ref

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    compute_client = holder.client

    instance_ref = self._ResolveInstance(holder, compute_client, args)
    log.Print(
        troubleshooter.Troubleshoot(instance_ref, self.ReleaseTrack().prefix))
    return

Troubleshoot.detailed_help = {
    'brief':
        'Troubleshoot issues with the setup of VM Manager on a specified VM '
        'instance',
    'DESCRIPTION':
        """
    *{command}* troubleshoots issues with the setup of VM Manager on a specified
    VM instance

    Troubleshoot checks if the OS Config API is enabled for the instance.
    """,
    'EXAMPLES': """
    To troubleshoot an instance named `my-instance` in zone `us-west1-a`, run

    $ *{command}* my-instance --zone=us-west1-a
    """
}
