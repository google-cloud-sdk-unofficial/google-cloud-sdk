# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""cloud-shell scp command."""


from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloud_shell import util
from googlecloudsdk.command_lib.cloud_shell.tunnel import CloudShellTunnel
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import log

FILE_TYPE = arg_parsers.RegexpValidator(
    r'^(cloudshell|localhost):.*$', 'must start with cloudshell: or localhost:')


def ToFileReference(path, remote):
  if path.startswith('cloudshell:'):
    return ssh.FileReference.FromPath(
        path.replace('cloudshell', str(remote), 1))
  elif path.startswith('localhost:'):
    return ssh.FileReference.FromPath(path.replace('localhost:', '', 1))
  else:
    raise ValueError('invalid path: ' + path)


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
@base.UniverseCompatible
class Scp(base.Command):
  """Copies files between Cloud Shell and the local machine."""

  detailed_help = {
      'DESCRIPTION':
          """\
        *{command}* copies files between your Cloud Shell instance and your
        local machine using the scp command.
        """,
      'EXAMPLES':
          """\
        To denote a file in Cloud Shell, prefix the file name with the string
        "cloudshell:" (e.g. _cloudshell:_~/_FILE_). To denote a local file,
        prefix the file name with the string "localhost:" (e.g.
        _localhost:_~/_FILE_). For example, to copy a remote directory to your
        local machine, run:

            $ {command} cloudshell:~/REMOTE-DIR localhost:~/LOCAL-DIR

        In the above example, *_~/REMOTE-DIR_* from your Cloud Shell instance is
        copied into the ~/_LOCAL-DIR_ directory.

        Conversely, files from your local computer can be copied into Cloud
        Shell:

            $ {command} localhost:~/LOCAL-FILE-1 localhost:~/LOCAL-FILE-2 \
cloudshell:~/REMOTE-DIR

        Under the covers, *scp(1)* or pscp (on Windows) is used to facilitate
        the transfer.
        """,
  }

  @staticmethod
  def Args(parser):
    util.ParseCommonArgs(parser)
    parser.add_argument(
        'sources',
        help='Specifies the files to copy.',
        type=FILE_TYPE,
        metavar='(cloudshell|localhost):SRC',
        nargs='+')
    parser.add_argument(
        'destination',
        help='Specifies a destination for the source files.',
        type=FILE_TYPE,
        metavar='(cloudshell|localhost):DEST')
    parser.add_argument(
        '--dry-run',
        help="""\
        If provided, prints the command that would be run to standard out
        instead of executing it.
        """,
        action='store_true')
    parser.add_argument(
        '--recurse',
        help='Upload directories recursively.',
        action='store_true')
    parser.add_argument(
        '--scp-flag',
        help='Extra flag to be sent to scp. This flag may be repeated.',
        action='append')

  def Run(self, args):
    connection_info = util.PrepareEnvironment(args)
    if not connection_info.web_host:
      raise FileNotFoundError(
          'Failed to get Cloud Shell web host. Environment might not be fully'
          ' initialized.'
      )
    jwt = util.GenerateAccessToken()
    tunnel = CloudShellTunnel(host=connection_info.web_host, jwt=jwt)
    tunnel.Start()
    remote = ssh.Remote(host='localhost', user=connection_info.user)
    command = ssh.SCPCommand(
        sources=[ToFileReference(src, remote) for src in args.sources],
        destination=ToFileReference(args.destination, remote),
        recursive=args.recurse,
        compress=False,
        port=str(tunnel.local_port),
        identity_file=connection_info.key,
        extra_flags=args.scp_flag,
        options={'StrictHostKeyChecking': 'no'},
    )
    # TODO(b/513021781): Cleanup AddPublicKey 410 fallback and direct SSH once
    # passwordless SSH is fully enforced.
    try:
      if args.dry_run:
        log.Print(' '.join(command.Build(connection_info.ssh_env)))
      else:
        try:
          command.Run(connection_info.ssh_env)
        except ssh.CommandError as exc:
          if connection_info.add_public_key_error:
            raise connection_info.add_public_key_error from exc
          raise
    finally:
      tunnel.Stop()
