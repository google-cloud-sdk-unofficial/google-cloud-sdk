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

import copy
import threading

from argcomplete.completers import FilesCompleter
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.compute.tpus.tpu_vm import exceptions as tpu_exceptions
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


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Scp(base.Command):
  """Copy files to and from a Cloud TPU VM via SCP."""

  # IAP and Batching are not available for GA.
  _ENABLE_IAP = False
  _ENABLE_BATCHING = False

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    ssh_utils.BaseSSHCLIHelper.Args(parser)
    tpu_ssh_utils.AddTPUSSHArgs(parser, cls._ENABLE_IAP, cls._ENABLE_BATCHING)
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
    release_track = self.ReleaseTrack()
    tpu = tpu_utils.TPUNode(release_track)
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

    if self._ENABLE_BATCHING:
      scp_batch_size = tpu_ssh_utils.ParseBatchSize(args.batch_size, worker_ips)

    tpu_ssh_utils.ValidateTPUState(node.state,
                                   tpu.messages.Node.StateValueValuesEnum)

    if node.health == tpu.messages.Node.HealthValueValuesEnum.UNHEALTHY_MAINTENANCE:
      raise tpu_exceptions.TPUInMaintenanceEvent()

    # Retrieve GuestAttributes.
    single_pod_worker = len(node.networkEndpoints) > 1 and len(worker_ips) == 1
    guest_attributes_response = (
        tpu_ssh_utils.GetGuestAttributes(tpu, single_pod_worker, worker_ips,
                                         tpu_name, args.zone))
    if guest_attributes_response is None:
      if (args.IsKnownAndSpecified('tunnel_through_iap') and
          args.tunnel_through_iap):
        log.debug('Unable to retrieve host information from guest attributes.')
        log.status.Print('Failed to connect to TPU.')
        log.status.Print(tpu_ssh_utils.IAP_TROUBLESHOOTING_HELP)
        raise tpu_exceptions.IapTunnelingUnavailable()
      log.debug('Unable to retrieve host keys from guest attributes. '
                'Continuing.')
      host_key_suffixes = None
    else:
      host_key_suffixes = (
          tpu_ssh_utils.GetHostKeySuffixesFromGuestAttributes(
              guest_attributes_response, single_pod_worker, worker_ips, node))

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
          instance_enable_oslogin=tpu_ssh_utils.TpuHasOsLoginEnabled(node),
          messages=base_classes.ComputeApiHolder(release_track).client.messages)
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

    instance_names = {}
    if (args.IsKnownAndSpecified('tunnel_through_iap') and
        args.tunnel_through_iap):
      # Retrieve the instance names from the GuestAttributes.
      for worker in worker_ips:
        # The GuestAttributes will only have one entry if we're targeting a
        # single worker.
        index = 0 if single_pod_worker else worker
        instance_name = tpu_ssh_utils.GetFromGuestAttributes(
            guest_attributes_response.guestAttributes, index, 'hostname')
        if instance_name is None:
          log.status.Print('Failed to connect to TPU.')
          log.status.Print(tpu_ssh_utils.IAP_TROUBLESHOOTING_HELP)
          raise tpu_exceptions.IapTunnelingUnavailable()
        instance_names[worker] = instance_name

    ssh_threads = []
    current_batch_size = 0
    exit_statuses = [None] * len(worker_ips)
    for worker, ips in worker_ips.items():
      # Make a copy of the destination for each worker so that concurrent
      # threads do not mutate the same object. b/238058396
      worker_dst = copy.deepcopy(dst)
      if worker_dst.remote:
        worker_dst.remote.host = ips.ip_address

      options = None
      if not args.plain:
        options = ssh_helper.GetConfig(
            tpu_ssh_utils.GetInstanceID(node.id, worker, host_key_suffixes),
            args.strict_host_key_checking, None)

      iap_tunnel_args = None
      if (args.IsKnownAndSpecified('tunnel_through_iap') and
          args.tunnel_through_iap):
        # Retrieve the instance name from the GuestAttributes.
        instance_name = instance_names[worker]
        iap_tunnel_args = tpu_ssh_utils.CreateSshTunnelArgs(
            args, self.ReleaseTrack(), project, args.zone, instance_name)

      cmd = ssh.SCPCommand(
          srcs,
          worker_dst,
          identity_file=identity_file,
          options=options,
          recursive=args.recurse,
          compress=args.compress,
          extra_flags=extra_flags,
          iap_tunnel_args=iap_tunnel_args)

      if args.dry_run:
        log.out.Print(' '.join(cmd.Build(ssh_helper.env)))
        continue

      # Orchestrate threading of scp commands based on number of workers, if
      # batching is enabled, and batch size
      if len(worker_ips) > 1:
        # Run the command on multiple workers concurrently.
        ssh_threads.append(
            threading.Thread(
                target=tpu_ssh_utils.AttemptRunWithRetries,
                args=('SCP', worker, exit_statuses, cmd, ssh_helper.env, None,
                      True, SCPRunCmd)))
        ssh_threads[-1].start()
        current_batch_size += 1
        if self._ENABLE_BATCHING and current_batch_size == scp_batch_size:
          tpu_ssh_utils.WaitForBatchCompletion(ssh_threads, exit_statuses)
          current_batch_size = 0
          ssh_threads = []
      else:
        # Run on a single worker.
        tpu_ssh_utils.AttemptRunWithRetries('SCP', worker, exit_statuses, cmd,
                                            ssh_helper.env, None, False,
                                            SCPRunCmd)

    if len(worker_ips) > 1 and ssh_threads:
      tpu_ssh_utils.WaitForBatchCompletion(ssh_threads, exit_statuses)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ScpAlpha(Scp):
  """Copy files to and from a Cloud TPU VM via SCP (Alpha)."""
  _ENABLE_IAP = True
  _ENABLE_BATCHING = True


Scp.detailed_help = {
    'brief':
        'Copy files to and from a Cloud TPU VM via SCP.',
    'EXAMPLES':
        """
        To copy a file (for example, a text file in the local home directory) to
        a Cloud TPU VM, run:

            $ {command} ~/my-file my-tpu:

        To copy a file into all workers in a Cloud TPU VM, run:

            $ {command} ~/my-file my-tpu: --worker=all

        To copy a file from a Cloud TPU VM to the home directory of the local
        computer, run:

            $ {command} my-tpu:~/my-file ~/

        To copy all files in a folder to a Cloud TPU VM, run:

            $ {command} ~/my-folder/ my-tpu: --recurse
        """
}
