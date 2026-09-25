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
"""Wrapper around gcloud compute ssh to collect SOS report from a GKE node."""

from __future__ import annotations

import datetime
import os
import sys
from typing import Any

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files

_REMOTE_SOSREPORT_CMD = (
    'OUTPUT=$(sudo sos report --all-logs --batch --tmp-dir=/var 2>&1) && '
    'FILE_PATH=$(echo "$OUTPUT" | '
    'grep -o "/var/sosreport-[^ ]*\\.tar\\.xz" | head -n 1) && '
    'sudo cat "$FILE_PATH" 2>/dev/null && '
    'sudo rm -f "$FILE_PATH"'
)


def _DefaultLocalFilename(node_name: str) -> str:
  """Generates a default timestamped filename for the collected archive."""
  # Strip optional [USER@] prefix if specified by the user (e.g. root@node-1).
  clean_node = node_name.split('@')[-1]
  timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
      '%Y%m%d-%H%M%S'
  )
  return 'sosreport-{0}-{1}.tar.xz'.format(clean_node, timestamp)


@base.UniverseCompatible
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ExportSosreport(base.Command):
  """Export an SOS report archive from a GKE node VM instance."""

  detailed_help = {
      'DESCRIPTION': """\
          Exports an SOS report archive from a Google Kubernetes Engine (GKE)
          node by wrapping `gcloud compute ssh`, executing a non-interactive
          SOS report command on the node, and saving the archive directly into
          a local file.
          """,
      'EXAMPLES': """\
          To export an SOS report from a node and save it to a local file:

            $ {command} gke-cluster-node-abcd

          To export from a node in a specific zone using IAP tunneling:

            $ {command} gke-cluster-node-abcd --zone=us-central1-a --tunnel-through-iap

          To save to a specific local file path:

            $ {command} gke-cluster-node-abcd --zone=us-central1-a --output-file=/tmp/node_report.tar.xz
          """,
  }

  @classmethod
  def Args(cls, parser: parser_arguments.ArgumentInterceptor) -> None:
    """Register command flags and re-use gcloud compute ssh flags."""
    parser.add_argument(
        'node_name',
        metavar='[USER@]NODE_NAME',
        completer=completers.InstancesCompleter,
        help=(
            'Specifies the GKE node (Compute Engine instance) to export the SOS'
            ' report from.'
        ),
    )

    parser.add_argument(
        '--output-file',
        help=(
            'Local destination path to write the SOS report archive. If'
            ' omitted, defaults to'
            ' ./sosreport-<NODE_NAME>-<TIMESTAMP>.tar.xz in the current'
            ' directory.'
        ),
    )

    # Re-use standard gcloud compute ssh flags
    ssh_utils.BaseSSHCLIHelper.Args(parser)
    compute_flags.AddZoneFlag(
        parser, resource_type='instance', operation_type='export sosreport from'
    )

    routing_group = parser.add_mutually_exclusive_group()
    routing_group.add_argument(
        '--internal-ip',
        action='store_true',
        default=False,
        help=(
            'Connect to instances using their internal IP addresses rather'
            ' than external IP.'
        ),
    )
    routing_group.add_argument(
        '--tunnel-through-iap',
        action='store_true',
        default=False,
        help=(
            'Tunnel the SSH connection through Cloud Identity-Aware Proxy for'
            ' TCP forwarding.'
        ),
    )

    parser.add_argument(
        '--ssh-flag',
        action='append',
        help='Additional flags to be passed to ssh(1).',
    )

  def Run(self, args: parser_extensions.Namespace) -> Any:
    """Executes the delegated compute ssh command and saves output to a file."""
    output_file = args.output_file or _DefaultLocalFilename(args.node_name)
    output_path = os.path.abspath(os.path.expanduser(output_file))

    # Base delegated compute ssh invocation
    ssh_cmd = [
        'compute',
        'ssh',
        args.node_name,
        '--command=' + _REMOTE_SOSREPORT_CMD,
        '--quiet',
    ]

    # Pass down all user-specified compute ssh flags
    specified_args = args.GetSpecifiedArgs()
    for flag, val in specified_args.items():
      # Only process flags and skip export-sosreport specific flags
      if not flag.startswith('--') or flag == '--output-file':
        continue
      if isinstance(val, bool):
        if val:
          ssh_cmd.append(flag)
      elif isinstance(val, list):
        for item in val:
          ssh_cmd.extend([flag, str(item)])
      elif val is not None:
        ssh_cmd.extend([flag, str(val)])

    if args.dry_run:
      log.status.Print('Dry run: Delegated SSH command:')
      return self.ExecuteCommandDoNotUse(ssh_cmd)

    log.status.Print(
        'Collecting SOS report from [{0}]...'.format(args.node_name)
    )
    log.status.Print('Saving archive to [{0}]...'.format(output_path))

    # Pipe the delegated SSH stdout directly into the destination file
    parent_dir = os.path.dirname(output_path)
    if parent_dir and not os.path.exists(parent_dir):
      files.MakeDir(parent_dir)

    exit_code = 0
    with files.BinaryFileWriter(output_path) as f:
      stdout_fd = sys.stdout.fileno()
      saved_stdout = os.dup(stdout_fd)
      try:
        os.dup2(f.fileno(), stdout_fd)
        exit_code = self.ExecuteCommandDoNotUse(ssh_cmd)
      finally:
        os.dup2(saved_stdout, stdout_fd)
        os.close(saved_stdout)

    if exit_code is not None and exit_code != 0:
      if os.path.exists(output_path):
        os.remove(output_path)
      raise core_exceptions.Error(
          'Failed to export SOS report from [{0}] (exit code {1}).'.format(
              args.node_name, exit_code
          )
      )

    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
      size_mb = os.path.getsize(output_path) / (1024.0 * 1024.0)
      log.status.Print(
          'Successfully collected SOS report: [{0}] ({1:.1f} MB)'.format(
              output_path, size_mb
          )
      )
    else:
      if os.path.exists(output_path):
        os.remove(output_path)
      raise core_exceptions.Error(
          'SOS report collection completed, but [{0}] was empty or not'
          ' found.'.format(output_path)
      )

    return output_path
