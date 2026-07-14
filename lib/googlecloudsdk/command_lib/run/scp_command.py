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
"""Base class for Cloud Run SCP commands."""

from googlecloudsdk.api_lib.run import ssh as run_ssh
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.util.ssh import ssh


class BaseScpCommand(base.Command):
  """Base class for Cloud Run SCP commands."""

  @staticmethod
  def AddBaseArgs(parser):
    """Add flags common to all SCP commands."""
    flags.AddContainerArg(parser)
    parser.add_argument(
        '--iap-tunnel-url-override',
        hidden=True,
        help=(
            'Allows for overriding the connection endpoint for integration'
            ' testing.'
        ),
    )

  def RunScp(
      self,
      args,
      workload_type,
      deployment_name,
      sources,
      destination,
  ):
    """Common Run logic for SCP commands."""
    args.project = flags.GetProjectID(args)
    args.region = flags.GetRegion(args, prompt=False)
    args.deployment_name = deployment_name
    args.release_track = self.ReleaseTrack()

    if not args.region:
      raise exceptions.ArgumentError(
          'Missing required argument [region]. Set --region flag or set'
          ' run/region property.'
      )

    if (
        args.release_track != base.ReleaseTrack.ALPHA
        and getattr(args, 'instance', None)
        and getattr(args, 'revision', None) is None
    ):
      raise exceptions.ArgumentError(
          'Revision must be specified with instance. Set --revision flag when'
          ' --instance flag is set.'
      )

    def FixRemote(file_ref):
      if file_ref.remote:
        # We don't really care what the user put as the host, we'll replace it
        # with the alias we use in SSH config.
        file_ref.remote.host = run_ssh.constants.SSH_HOST_KEY_ALIAS
        # Also ensure the user is 'root' as Cloud Run SSH only supports root.
        file_ref.remote.user = run_ssh.constants.SSH_ROOT_USER
      return file_ref

    ssh.SCPCommand.Verify(sources, destination, single_remote=True)
    sources = [FixRemote(s) for s in sources]
    destination = FixRemote(destination)

    return run_ssh.Ssh(args, workload_type).RunScp(
        sources=sources,
        destination=destination,
        recursive=getattr(args, 'recurse', False),
        compress=getattr(args, 'compress', False),
        extra_flags=getattr(args, 'scp_flag', None),
    )
