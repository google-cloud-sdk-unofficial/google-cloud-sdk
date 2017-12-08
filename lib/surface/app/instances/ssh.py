# Copyright 2017 Google Inc. All Rights Reserved.
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

"""The `app instances ssh` command."""

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import exceptions as api_exceptions
from googlecloudsdk.api_lib.app import util
from googlecloudsdk.api_lib.app import version_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import exceptions as command_exceptions
from googlecloudsdk.command_lib.util import ssh
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io


ENABLE_DEBUG_WARNING = """\
This instance is serving live application traffic.  Any changes made could
result in downtime or unintended consequences."""


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Ssh(base.Command):
  """SSH into the VM of an App Engine Flexible instance."""

  detailed_help = {
      'DESCRIPTION': """\
        *{command}* lets you remotely log in to your running App Engine Flexible
        instances. It resolves the instance's IP address and pre-populates the
        VM with a public key managed by gcloud.

        If the gcloud managed key pair does not exist, it is generated the first
        time an SSH command is run -- this may prompt you for a passphrase for
        private key encryption.

        All SSH commands require the OpenSSH client suite to be installed on
        Linux and Mac OS X. Windows does not have any external requirements.
        It has a PuTTY suite is bundled with gcloud instead.""",
      'EXAMPLES': """\
          To SSH into an App Engine Flexible instance, run:

              $ {command} --service s1 --version v1 i1

          To SSH into the app container within an instance, run:

              $ {command} --service s1 --version v1 i1 --container=gaeapp
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'instance',
        help='The instance ID.')
    parser.add_argument(
        '--service', '-s',
        required=True,
        help='The service ID.')
    parser.add_argument(
        '--version', '-v',
        required=True,
        help='The version ID.')
    parser.add_argument(
        '--container',
        help='Name of the container within the VM to connect to.')

  def Run(self, args):
    """Connect to a running flex instance.

    Args:
      args: argparse.Namespace, the args the command was invoked with.

    Raises:
      InvalidInstanceTypeError: The instance is not supported for SSH.
      MissingVersionError: The version specified does not exist.
      MissingInstanceError: The instance specified does not exist.
      UnattendedPromptError: Not running in a tty.
      OperationCancelledError: User cancelled the operation.
      ssh.CommandError: The SSH command exited with SSH exit code, which
        usually implies that a connection problem occurred.

    Returns:
      int, The exit code of the SSH command.
    """
    env = ssh.Environment.Current()
    env.RequireSSH()
    keys = ssh.Keys.FromFilename()

    api_client = appengine_api_client.GetApiClient()
    try:
      version = api_client.GetVersionResource(
          service=args.service, version=args.version)
    except api_exceptions.NotFoundError:
      raise command_exceptions.MissingVersionError(
          '{}/{}'.format(args.service, args.version))
    version = version_util.Version.FromVersionResource(version, None)
    if version.environment is not util.Environment.FLEX:
      if version.environment is util.Environment.MANAGED_VMS:
        environment = 'Managed VMs'
        msg = 'Use `gcloud compute ssh` for Managed VMs instances.'
      else:
        environment = 'Standard'
        msg = None
      raise command_exceptions.InvalidInstanceTypeError(environment, msg)
    res = resources.REGISTRY.Parse(
        args.instance,
        params={'versionsId': args.version,
                'instancesId': args.instance,
                'servicesId': args.service},
        collection='appengine.apps.services.versions.instances')
    rel_name = res.RelativeName()
    try:
      instance = api_client.GetInstanceResource(res)
    except api_exceptions.NotFoundError:
      raise command_exceptions.MissingInstanceError(rel_name)

    if not instance.vmDebugEnabled:
      log.warn(ENABLE_DEBUG_WARNING)
      console_io.PromptContinue(cancel_on_no=True, throw_if_unattended=True)
    user = ssh.GetDefaultSshUsername()
    public_key = keys.GetPublicKey().ToEntry()
    ssh_key = '{user}:{key} {user}'.format(user=user, key=public_key)
    log.status.Print('Sending public key to instance [{}].'.format(rel_name))
    api_client.DebugInstance(res, ssh_key)
    options = {
        'IdentitiesOnly': 'yes',  # No ssh-agent as of yet
        'UserKnownHostsFile': ssh.KnownHosts.DEFAULT_PATH}
    cmd = ssh.SSHCommand(
        instance.vmIp, user=user, identity_file=keys.key_file, options=options)
    if args.container:
      cmd.tty = True
      cmd.remote_command = ['container_exec', args.container, '/bin/sh']
    return cmd.Run(env)

