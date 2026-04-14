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
"""Command to SSH into a Cloud Run service."""

from googlecloudsdk.api_lib.run import ssh as run_ssh
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import ssh_command


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.Hidden
@base.DefaultUniverseOnly
class Ssh(ssh_command.BaseSshCommand):
  """SSH into a service instance."""

  detailed_help = {
      'DESCRIPTION': """\
          Starts a secure, interactive shell session with an instance of a Cloud Run service.
          """,
      'EXAMPLES': """\
          To start an interactive shell session with a Cloud Run service:

              $ {command} my-service --instance=my-instance-id
          """,
  }

  _support_revision = True

  @classmethod
  def Args(cls, parser):
    # Add flags for targeting a specific instance and container.
    flags.AddInstanceArg(parser)
    cls.AddBaseArgs(parser)
    # Add the revision flag if supported.
    if cls._support_revision:
      flags.AddRevisionArg(parser)
    # Add the service name as a required positional argument.
    parser.add_argument(
        'service',
        help='The name of the service to SSH into.',
    )

  def Run(self, args):
    """Connect to a running Cloud Run service deployment."""
    self.RunSsh(
        args,
        run_ssh.Ssh.WorkloadType.SERVICE,
        args.service,
        getattr(args, 'instance', None),
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
@base.DefaultUniverseOnly
class SshAlpha(Ssh):
  """SSH into a service instance."""

  _support_revision = False
