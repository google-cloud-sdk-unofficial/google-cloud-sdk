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
"""Command to tail logs for a Cloud Run instance."""

import subprocess
import sys

from googlecloudsdk.api_lib.run import ssh as run_ssh
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import log_tailer
from googlecloudsdk.core import exceptions as core_exceptions


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Tail(base.Command):
  """Tail logs for a Cloud Run instance."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          {command} tails log entries for a particular Cloud Run instance
          in real time. The log entries are formatted for consumption in a
          terminal.
          """
      ),
      'EXAMPLES': (
          """\
          To tail log entries for a Cloud Run instance, run:

            $ {command} my-instance
          """
      ),
  }

  @classmethod
  def Args(cls, parser):
    flags.AddContainerArg(parser)
    parser.add_argument(
        '--iap-tunnel-url-override',
        hidden=True,
        help=(
            'Allows for overriding the connection endpoint for integration'
            ' testing.'
        ),
    )
    parser.add_argument('instance', help='Name for a Cloud Run instance.')

  def _StreamLogs(self, ssh_cmd, env):
    """Executes the SSH command and streams filtered log lines."""
    cmd = ssh_cmd.Build(env)
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    try:
      for line in iter(process.stdout.readline, ''):
        if log_tailer.IsUnsupportedLogTailingError(line):
          raise core_exceptions.Error(log_tailer.LOG_TAILING_NOT_SUPPORTED_MSG)
        line = log_tailer.FormatLogLineForTail(line)
        sys.stdout.write(line)
        sys.stdout.flush()
    except KeyboardInterrupt:
      pass
    finally:
      if process.poll() is None:
        process.terminate()
        try:
          process.wait(timeout=2)
        except subprocess.TimeoutExpired:
          process.kill()
    return process.poll() or 0

  def Run(self, args):
    """Executes the tail logs command on the target instance."""
    args.project = flags.GetProjectID(args)
    args.region = flags.GetRegion(args, prompt=True)
    if not args.region:
      raise exceptions.ArgumentError(
          'Missing required argument [region]. Set --region flag or set'
          ' run/region property.'
      )

    # run_ssh.Ssh uses deployment_name as the primary resource identifier
    # across all workload types, expecting instance to be None.
    args.deployment_name = args.instance
    args.instance = None
    args.release_track = self.ReleaseTrack()

    ssh_instance = run_ssh.Ssh(args, run_ssh.Ssh.WorkloadType.INSTANCE)
    components = ssh_instance.GetSshCommandComponents()

    ssh_cmd = run_ssh.ssh.SSHCommand(
        remote=components.remote,
        cert_file=components.cert_file,
        iap_tunnel_args=components.iap_tunnel_args,
        options=components.options,
        identity_file=components.identity_file,
        remote_command=[
            log_tailer.UNSUPPORTED_LIB,
            log_tailer.TAIL_LOGS_BIN,
        ],
    )
    return self._StreamLogs(ssh_cmd, components.env)
