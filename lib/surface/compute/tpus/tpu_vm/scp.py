# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command to SCP to/from a Cloud TPU VM Node."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import threading

from argcomplete.completers import FilesCompleter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.compute.tpus.tpu_vm import ssh as tpu_ssh_utils
from googlecloudsdk.command_lib.compute.tpus.tpu_vm import util as tpu_utils
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def AddSCPArgs(parser):
  """Additional flags and positional args to be passed to *scp(1)*."""
  parser.add_argument(
      '--scp-flag',
      action='append',
      help="""\
      Additional flags to be passed to *scp(1)*. This flag may be repeated.
      """)

  parser.add_argument(
      'sources',
      completer=FilesCompleter,
      help='Specifies the files to copy.',
      metavar='[[USER@]INSTANCE:]SRC',
      nargs='+')

  parser.add_argument(
      'destination',
      help='Specifies a destination for the source files.',
      metavar='[[USER@]INSTANCE:]DEST')

  parser.add_argument(
      '--recurse', action='store_true', help='Upload directories recursively.')

  parser.add_argument(
      '--compress', action='store_true', help='Enable compression.')


def SCPRunCmd(env, cmd, *args):
  """Returns a function to run."""
  del args
  return cmd.Run(env, force_connect=True)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Scp(base.Command):
  """SCP into a Cloud TPU VM."""

  @staticmethod
  def Args(parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    ssh_utils.BaseSSHCLIHelper.Args(parser)
    tpu_ssh_utils.AddTPUSSHArgs(parser)
    AddSCPArgs(parser)
    flags.AddZoneFlag(parser, resource_type='tpu', operation_type='scp')

  def Run(self, args):
    dst = ssh.FileReference.FromPath(args.destination)
    srcs = [ssh.FileReference.FromPath(src) for src in args.sources]
    ssh.SCPCommand.Verify(srcs, dst, single_remote=True)
    if dst.remote:
      tpu_name = dst.remote.host
    else:
      tpu_name = srcs[0].remote.host

    # If zone is not set, retrieve the one from the config.
    if args.zone is None:
      args.zone = properties.VALUES.compute.zone.Get(required=True)

    # Retrieve the node.
    tpu = tpu_utils.TPUNode()
    node = tpu.Get(tpu_name, args.zone)
    if not tpu_utils.IsTPUVMNode(node):
      raise exceptions.BadArgumentException(
          'TPU',
          'this command is only available for Cloud TPU VM nodes. To access '
          'this node, please see '
          'https://cloud.google.com/tpu/docs/creating-deleting-tpus.')

    worker_ips = tpu_ssh_utils.ParseWorkerFlag(args.worker,
                                               node.networkEndpoints,
                                               args.internal_ip)

    if len(worker_ips) > 1 and srcs[0].remote:
      raise exceptions.InvalidArgumentException(
          '--worker', 'cannot target multiple workers while copying files to '
          'client.')

    tpu_ssh_utils.ValidateTPUState(node.state,
                                   tpu.messages.Node.StateValueValuesEnum)

    host_key_suffixes = tpu_ssh_utils.GetHostKeySuffixes(
        tpu, tpu_name, worker_ips, len(node.networkEndpoints), args.zone)

    # Generate the public key.
    ssh_helper = ssh_utils.BaseSSHCLIHelper()
    ssh_helper.Run(args)
    public_key = ssh_helper.keys.GetPublicKey().ToEntry()

    remote = dst.remote or srcs[0].remote
    if not dst.remote:  # Make sure all remotes point to the same ref.
      for src in srcs:
        src.remote = remote

    if remote.user:
      username_requested = True
    else:
      username_requested = False
      remote.user = ssh.GetDefaultSshUsername(warn_on_account_user=True)

    project = tpu_utils.GetProject(self.ReleaseTrack(), ssh_helper)

    if not args.plain:
      # If there is an '@' symbol in the user_host arg, the user is requesting
      # to connect as a specific user. This may get overridden by OS Login.
      _, expiration_micros = ssh_utils.GetSSHKeyExpirationFromArgs(args)
      oslogin_state = ssh.GetOsloginState(
          None,
          project,
          remote.user,
          public_key,
          expiration_micros,
          self.ReleaseTrack(),
          username_requested=username_requested,
          instance_enable_oslogin=tpu_ssh_utils.TpuHasOsLoginEnabled(node))
      remote.user = oslogin_state.user

    # Format the key correctly.
    public_key = '{1}:{0} {1}'.format(public_key, remote.user)
    if not args.plain and not args.dry_run:
      tpu_ssh_utils.AddSSHKeyIfNeeded(project, tpu, node, tpu_name, args.zone,
                                      public_key)

    identity_file = None
    if not args.plain:
      identity_file = ssh_helper.keys.key_file
      # If the user's key is not in the SSH agent, the command will stall. We
      # want to verify it is added before proceeding, and raise an error if it
      # is not.
      if not args.dry_run and len(worker_ips) > 1:
        tpu_ssh_utils.VerifyKeyInAgent(identity_file)

    extra_flags = []

    if args.scp_flag:
      extra_flags.extend(args.scp_flag)

    ssh_threads = []
    for worker, ips in worker_ips.items():
      options = None
      if not args.plain:
        options = ssh_helper.GetConfig(
            tpu_ssh_utils.GetInstanceID(node.id, worker, host_key_suffixes),
            args.strict_host_key_checking, None)

      remote.host = ips.ip_address
      cmd = ssh.SCPCommand(
          srcs,
          dst,
          identity_file=identity_file,
          options=options,
          recursive=args.recurse,
          compress=args.compress,
          extra_flags=extra_flags)

      if args.dry_run:
        log.out.Print(' '.join(cmd.Build(ssh_helper.env)))
        continue

      if len(worker_ips) > 1:
        # Run the command on multiple workers concurrently.
        ssh_threads.append(
            threading.Thread(
                target=tpu_ssh_utils.AttemptRunWithRetries,
                args=('SCP', worker, cmd, ssh_helper.env, None, True,
                      SCPRunCmd)))
        ssh_threads[-1].start()
      else:
        # Run on a single worker.
        tpu_ssh_utils.AttemptRunWithRetries('SCP', worker, cmd, ssh_helper.env,
                                            None, False, SCPRunCmd)
