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

from googlecloudsdk.api_lib.run import ssh as run_ssh
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags


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
            '/lib64/ld-linux-x86-64.so.2',
            '/usr/local/gcp/bin/tail_logs',
        ],
    )
    return ssh_cmd.Run(components.env)
