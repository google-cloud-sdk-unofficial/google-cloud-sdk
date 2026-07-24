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
"""cloud-shell ssh command."""

import datetime
import shlex
import threading
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloud_shell import util
from googlecloudsdk.command_lib.cloud_shell.tunnel import CloudShellTunnel
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
@base.UniverseCompatible
class Ssh(base.Command):
  """Allows you to establish an interactive SSH session with Cloud Shell."""

  detailed_help = {
      'DESCRIPTION': (
          """\
        *{command}* lets you remotely log in to Cloud Shell. If your Cloud Shell
        is not currently running, this will cause it to be started before
        establishing the SSH session.
        """
      ),
      'EXAMPLES': (
          """\
        To SSH into your Cloud Shell, run:

            $ {command}

        To run a remote command in your Cloud Shell, run:

            $ {command} --command=ls
        """
      ),
  }

  @staticmethod
  def Args(parser):
    util.ParseCommonArgs(parser)
    parser.add_argument(
        '--command',
        help="""\
        A command to run in Cloud Shell.

        Runs the command in Cloud Shell and then exits.
        """,
    )
    parser.add_argument(
        '--dry-run',
        help="""\
        If provided, prints the command that would be run to standard out
        instead of executing it.
        """,
        action='store_true',
    )
    parser.add_argument(
        '--ssh-flag',
        help='Additional flags to be passed to *ssh(1)*.',
        action='append',
    )
    parser.add_argument(
        '--authorize-session',
        help="""\
        If provided, sends OAuth credentials to the current Cloud Shell session
        on behalf of the user. When this completes, the session will be
        authorized to run various Google Cloud command-line tools without
        requiring the user to manually authenticate.
        """,
        action='store_true',
    )

  def Run(self, args):
    if not args.authorize_session:
      log.Print(
          'Automatic authentication with GCP CLI tools in Cloud Shell is '
          'disabled. To enable, please rerun command with '
          '`--authorize-session` flag.'
      )
    command_list = args.command.split(' ') if args.command else ['bash -l']
    project = properties.VALUES.core.project.Get()
    connection_info = util.PrepareEnvironment(args)
    if args.authorize_session:
      util.AuthorizeEnvironment()
    if not connection_info.web_host:
      raise FileNotFoundError(
          'Failed to get Cloud Shell web host. Environment might not be fully'
          ' initialized.'
      )
    jwt = util.GenerateAccessToken()

    def _open_tunnel(port: int):
      """Attempts to open a tunnel to Cloud Shell."""
      tunnel = None
      try:
        log.debug('Attempting passwordless SSH on port %d (tunnel)...', port)
        tunnel = CloudShellTunnel(
            host=connection_info.web_host,
            jwt=jwt,
            remote_port=port,
            log_errors_as_debug=True,
        )
        tunnel.Start()
        return tunnel
      except Exception as e:  # pylint: disable=broad-except
        log.debug('Tunnel to %d failed: %s', port, e)
        if tunnel:
          tunnel.Stop()
        raise

    def _ssh_connect(port: int, project: str, use_key: bool, use_tunnel: bool):
      """Attempts to connect to Cloud Shell via SSH."""

      connection_info = (
          util.PrepareEnvironment(args)
          if use_key
          else util.PrepareEnvironmentNoKey(args)
      )
      target = 'localhost' if use_tunnel else connection_info.host

      command = ssh.SSHCommand(
          remote=ssh.Remote(host=target, user=connection_info.user),
          port=str(port),
          identity_file=connection_info.key if use_key else None,
          remote_command=([f'DEVSHELL_PROJECT_ID={project}'] if project else [])
          + command_list,
          extra_flags=args.ssh_flag,
          tty=not args.command,
          options={
              'StrictHostKeyChecking': 'no',
              'PubkeyAuthentication': 'yes' if use_key else 'no',
              'PreferredAuthentications': (
                  'publickey' if use_key else 'password'
              ),
              'BatchMode': 'yes',
              'LogLevel': 'QUIET',
          },
          remainder=getattr(args, 'ssh_args', None),
      )
      if args.dry_run:
        log.Print(
            ' '.join([
                shlex.quote(elem)
                for elem in command.Build(connection_info.ssh_env)
            ])
        )
        return
      self._RunCommand(command, connection_info.ssh_env, args)
      return

    # 1. Attempt TCP tunnel noauth login to port 22
    tunnel22 = None
    try:
      tunnel22 = _open_tunnel(22)
      return _ssh_connect(
          port=tunnel22.local_port,
          project=project,
          use_key=False,
          use_tunnel=True,
      )
    except Exception:  # pylint: disable=broad-except
      pass  # no logs
    finally:
      if tunnel22:
        tunnel22.Stop()

    # 2. Attempt TCP tunnel noauth login to port 2222
    tunnel2222 = None
    try:
      tunnel2222 = _open_tunnel(2222)
      return _ssh_connect(
          port=tunnel2222.local_port,
          project=project,
          use_key=False,
          use_tunnel=True,
      )
    except Exception:  # pylint: disable=broad-except
      pass  # no logs
    finally:
      if tunnel2222:
        tunnel2222.Stop()

    # 3. Attempt conventional AddPublicKey tunneled login to port 22
    tunnel22 = None
    try:
      tunnel22 = _open_tunnel(22)
      return _ssh_connect(
          port=tunnel22.local_port,
          project=project,
          use_key=True,
          use_tunnel=True,
      )
    finally:
      if tunnel22:
        tunnel22.Stop()

  def _RunCommand(self, command, ssh_env, args):
    if args.authorize_session:
      self.done = threading.Event()
      thread = threading.Thread(target=self.Reauthorize, args=(), daemon=True)
      thread.start()
      try:
        command.Run(ssh_env)
      finally:
        self.done.set()
    else:
      command.Run(ssh_env)

  def Reauthorize(self):
    while not self.done.is_set():
      self.done.wait(
          (
              util.MIN_CREDS_EXPIRY - datetime.timedelta(minutes=2)
          ).total_seconds()
      )
      if not self.done.is_set():
        util.AuthorizeEnvironment()


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SshAlpha(Ssh):
  """Allows you to establish an interactive SSH session with Cloud Shell."""

  @staticmethod
  def Args(parser):
    Ssh.Args(parser)
    util.AddSshArgFlag(parser)
