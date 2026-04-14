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
"""Command to SSH into a Cloud Run instance."""

from googlecloudsdk.api_lib.run import ssh as run_ssh
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import ssh_command


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
@base.DefaultUniverseOnly
class Ssh(ssh_command.BaseSshCommand):
  """SSH into an instance."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          Starts a secure, interactive shell session with a Cloud Run instance.
          """
      ),
      'EXAMPLES': (
          """\
          To start an interactive shell session with a Cloud Run instance:

              $ {command} my-instance
          """
      ),
  }

  @classmethod
  def Args(cls, parser):
    cls.AddBaseArgs(parser)
    # Add the instance name as a required positional argument.
    parser.add_argument(
        'instance',
        help='The name of the instance to SSH into.',
    )

  def Run(self, args):
    """Connect to a running Cloud Run instance deployment."""
    # For instances, the positional 'instance' is the deployment name.
    self.RunSsh(args, run_ssh.Ssh.WorkloadType.INSTANCE, args.instance)
