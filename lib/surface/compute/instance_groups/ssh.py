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
from googlecloudsdk.command_lib.compute import iap_tunnel
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute import ssh_utils as compute_ssh_utils
from googlecloudsdk.command_lib.compute.instance_groups import flags as ig_flags
from googlecloudsdk.command_lib.compute.instance_groups import ssh_utils
from googlecloudsdk.core.util import files
from surface.compute import ssh as compute_ssh


def AddSshFlags(parser):
  """Adds SSH flags for the compute instance-groups ssh command."""
  parser.add_argument(
      '--command',
      required=True,
      help=textwrap.dedent("""
        Command to run concurrently on all instances in the specified Instance
        Group (unless `--batch-size` is specified). Runs the command on each
        target instance and then exits.
      """),
  )
  parser.add_argument(
      '--user',
      help=textwrap.dedent("""
        Username with which to SSH into the instances. If omitted, the default
        login user is used.
      """),
  )
  parser.add_argument(
      '--batch-size',
      default='all',
      help=textwrap.dedent("""
        Batch size for simultaneous command execution on the client's side.
        This flag takes a value greater than 0 to specify the batch size to
        control concurrent connections, or the special keyword ``all'' to allow
        concurrent command execution on all instances in the Instance Group.
        If the command fails on any instance in a batch, subsequent batches are
        not executed.
      """),
  )
  parser.add_argument(
      '--output-directory',
      help=textwrap.dedent("""
        Path to the directory to output the logs of the commands.

        The path can be relative or absolute. The directory must already exist.

        If not specified, standard output will be used.

        The logs will be written in files named {INSTANCE_NAME}.log.
      """),
  )
  compute_ssh.AddContainerArg(parser)
  parser.add_argument(
      '--ssh-flag',
      action='append',
      help=textwrap.dedent("""
        Additional flags to be passed to *ssh(1)*. It is recommended that flags
        be passed using an assignment operator and quotes.

        This flag will replace occurrences of ``%USER%'', ``%INSTANCE%'',
        ``%INTERNAL%'', ``%NAME%'', ``%ZONE%'', and ``%PROJECT%'' with their
        dereferenced values for each target instance. ``%NAME%'', ``%ZONE%'',
        and ``%PROJECT%'' are replaced with the instance name, zone, and project
        ID respectively. If connecting to the instance's external IP, then
        ``%INSTANCE%'' is replaced with that, otherwise it is replaced with the
        internal IP. ``%INTERNAL%'' is always replaced with the internal
        IP of the instance.
      """),
  )
  routing_group = parser.add_mutually_exclusive_group()
  compute_ssh.AddInternalIPArg(routing_group)
  iap_tunnel.AddSshTunnelArgs(parser, routing_group)


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
