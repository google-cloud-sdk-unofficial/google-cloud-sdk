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

"""Command to SSH into instances in a Compute Engine Instance Group."""

import os
import textwrap

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute import ssh_utils as compute_ssh_utils
from googlecloudsdk.command_lib.compute.instance_groups import flags as ig_flags
from googlecloudsdk.command_lib.compute.instance_groups import ssh_utils
from googlecloudsdk.core.util import files


def AddSshFlags(parser):
  """Adds SSH flags for the compute instance-groups ssh command."""
  ssh_utils.AddSshFlags(parser)


DETAILED_HELP = {
    'brief': 'SSH into instances of a Compute Engine instance group.',
    'DESCRIPTION': textwrap.dedent("""
        *{command}* runs an SSH command concurrently on all running Compute
        Engine VM instances in a specified Instance Group (managed or unmanaged;
        unless `--batch-size` is specified).

        Within a batch, all instances are executed concurrently even if the
        command fails on some instances. When executing across multiple batches
        (via `--batch-size`), if the command fails on any instance in a batch,
        subsequent batches are not executed. After execution completes, a
        summary of succeeded, failed (with their exit codes), and skipped
        instances (formatted by batch when multiple batches are used) is
        printed to standard error. If the command succeeds on all target
        instances, *{command}* exits with status `0`. If the command fails on
        one or more instances, *{command}* exits with the first non-zero exit
        status encountered (`255` for SSH connection or client errors, or the
        remote command's non-zero exit code).
        """),
    'EXAMPLES': textwrap.dedent("""
        To run an SSH command concurrently on all instances in Instance Group
        `my-group` in zone `us-central1-a`, run:

          $ {command} my-group --zone=us-central1-a --command="hostname"

        To run an SSH command with a custom batch size on a regional Managed
        Instance Group `my-regional-mig` in region `us-central1`, run:

          $ {command} my-regional-mig --region=us-central1 \\
              --command="uptime" --batch-size=4
        """),
}


@base.RegionalEndpointsSupported
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Ssh(base.Command):
  """SSH into instances of a Compute Engine instance group."""

  @classmethod
  def Args(cls, parser):
    """Specifies command flags."""
    ig_flags.MULTISCOPE_INSTANCE_GROUP_ARG.AddArgument(parser)
    compute_ssh_utils.BaseSSHCLIHelper.Args(parser)
    AddSshFlags(parser)

  def Run(self, args):
    """Executes the SSH command on all instances in the instance group."""
    if args.output_directory:
      output_directory_path = os.path.abspath(
          files.ExpandHomeDir(args.output_directory)
      )
      if not os.path.isdir(output_directory_path):
        raise exceptions.InvalidArgumentException(
            '--output-directory',
            f'Failed to find directory {output_directory_path}. Please create '
            'it or specify another directory.',
        )

    holder = base_classes.ComputeApiHolder(base.ReleaseTrack.GA)
    client = holder.client
    ig_ref = ig_flags.MULTISCOPE_INSTANCE_GROUP_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=compute_scope.ScopeEnum.ZONE,
        scope_lister=compute_flags.GetDefaultScopeLister(client),
    )

    instance_refs = ssh_utils.ListInstanceRefs(holder, ig_ref)
    if not instance_refs:
      raise exceptions.BadArgumentException(
          'NAME',
          f'No running instances found in instance group [{ig_ref.Name()}].',
      )

    ssh_utils.RunSshOnInstances(self, args, instance_refs)


Ssh.detailed_help = DETAILED_HELP
