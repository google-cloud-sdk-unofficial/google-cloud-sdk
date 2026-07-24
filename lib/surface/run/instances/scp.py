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
"""Command to scp into a Cloud Run instance."""

from googlecloudsdk.api_lib.run import ssh as run_ssh
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import scp_command


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
@base.DefaultUniverseOnly
class Scp(scp_command.BaseScpCommand):
  """A command to copy files to and from a Cloud Run instance."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          Securely copies files between a Cloud Run instance and your local machine using the scp command.
          """
      ),
      'EXAMPLES': (
          """\
          To copy a local file to a Cloud Run instance:

              $ {command} my-local-file my-instance:/tmp/my-remote-file

          To copy a remote file from a Cloud Run instance:

              $ {command} my-instance:/tmp/my-remote-file my-local-file
          """
      ),
  }

  _support_revision = False

  @classmethod
  def Args(cls, parser):
    cls.AddBaseArgs(parser)

    parser.add_argument(
        'sources',
        metavar='LOCAL_FILE|INSTANCE:REMOTE_FILE',
        nargs='+',
        help='The files to copy.',
    )
    parser.add_argument(
        'destination',
        metavar='LOCAL_FILE|INSTANCE:REMOTE_FILE',
        help='The destination to copy to.',
    )
    parser.add_argument(
        '--recurse', action='store_true', help='Copy directories recursively.'
    )
    parser.add_argument(
        '--compress', action='store_true', help='Enable compression.'
    )
    parser.add_argument(
        '--scp-flag',
        action='append',
        help='Extra flag to be sent to scp. This flag may be repeated.',
    )

  def Run(self, args):
    """Copy files to or from a Cloud Run instance."""
    sources = [run_ssh.ssh.FileReference.FromPath(s) for s in args.sources]
    destination = run_ssh.ssh.FileReference.FromPath(args.destination)

    instance_name = None
    if destination.remote:
      instance_name = destination.remote.host
    else:
      for s in sources:
        if s.remote:
          instance_name = s.remote.host
          break

    if not instance_name:
      raise exceptions.ArgumentError(
          'At least one of the sources or the destination must be remote (e.g.'
          ' INSTANCE:PATH)'
      )

    return self.RunScp(
        args,
        run_ssh.Ssh.WorkloadType.INSTANCE,
        instance_name,
        sources,
        destination,
    )
