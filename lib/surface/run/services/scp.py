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
"""Command to scp into a Cloud Run service."""

from googlecloudsdk.api_lib.run import ssh as run_ssh
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import scp_command


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
@base.Hidden
@base.DefaultUniverseOnly
class Scp(scp_command.BaseScpCommand):
  """A command to copy files to and from a Cloud Run service."""

  detailed_help = {
      'DESCRIPTION': (
          """\
          Securely copies files between a Cloud Run service and your local machine using the scp command.
          """
      ),
      'EXAMPLES': (
          """\
          To copy a local file to a Cloud Run service:

              $ {command} my-local-file my-service:/tmp/my-remote-file

          To copy a remote file from a Cloud Run service:

              $ {command} my-service:/tmp/my-remote-file my-local-file
          """
      ),
  }

  _support_revision = True

  @classmethod
  def Args(cls, parser):
    # Add flags for targeting a specific instance.
    flags.AddInstanceArg(parser)
    cls.AddBaseArgs(parser)

    # Add the revision flag if supported.
    if cls._support_revision:
      flags.AddRevisionArg(parser)

    parser.add_argument(
        'sources',
        metavar='LOCAL_FILE|SERVICE:REMOTE_FILE',
        nargs='+',
        help='The files to copy.',
    )
    parser.add_argument(
        'destination',
        metavar='LOCAL_FILE|SERVICE:REMOTE_FILE',
        help='The destination to copy to.',
    )
    parser.add_argument(
        '--recurse', action='store_true', help='Upload directories recursively.'
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
    """Copy files to or from a Cloud Run service."""
    sources = [run_ssh.ssh.FileReference.FromPath(s) for s in args.sources]
    destination = run_ssh.ssh.FileReference.FromPath(args.destination)

    service_name = None
    if destination.remote:
      service_name = destination.remote.host
    else:
      for s in sources:
        if s.remote:
          service_name = s.remote.host
          break

    if not service_name:
      raise exceptions.ArgumentError(
          'At least one of the sources or the destination must be remote (e.g.'
          ' SERVICE:PATH)'
      )

    return self.RunScp(
        args,
        run_ssh.Ssh.WorkloadType.SERVICE,
        service_name,
        sources,
        destination,
    )
