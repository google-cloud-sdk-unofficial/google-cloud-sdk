# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Connects to a serial port gateway using SSH."""

import argparse
import getpass
import sys

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags
from googlecloudsdk.command_lib.util import ssh

from googlecloudsdk.core import http
from googlecloudsdk.core import log

SERIAL_PORT_GATEWAY = 'ssh-serialport.googleapis.com'
CONNECTION_PORT = '9600'
HOST_KEY_URL = ('https://cloud-certs.storage.googleapis.com/'
                'google-cloud-serialport-host-key.pub')
DEFAULT_HOST_KEY = ('ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDkOOCaBZVTxzvjJ7+7'
                    'YonnZOwIZ2Z7azwPC+oHbBCbWNBZAwzs63JQlHLibHG6NiNunFwP/lWs'
                    '5SpLx5eEdxGL+WQmvtldnBdqJzNE1UHrxPDegysCXxn1fT7KELpLozLh'
                    'vlfSnWJXbFbDrGB0bTv2U373Zo3BL9XTRf3qthdDEMF3GouUH8pGvitH'
                    'lwcwO1ulpVB0sTIdB7Bu+YPuo1XSuL2n3tXA9n9S+7kQCoyuXodeBpJo'
                    'JxzdJeoQXAepLrLA7nl6jRiYZyic0WJeSJm7vmvl1VDAGkyXloNEhBnv'
                    'oQFQl5aCwcS8UQnzzwMDflQ+JgsynYN08dLIRGcwkJe9')
SERIAL_PORT_HELP = ('https://cloud.google.com/compute/docs/'
                    'instances/interacting-with-serial-console')


class ConnectToSerialPort(ssh_utils.BaseSSHCLICommand):
  """Class for connecting through a gateway to the interactive serial port."""

  @staticmethod
  def Args(parser):
    # Use BaseSSHCommand args here, since we don't want --plain or
    # --strict-host-key-checking.
    ssh_utils.BaseSSHCommand.Args(parser)

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help=('If provided, the ssh command is printed to standard out '
              'rather than being executed.'))

    # This flag should be hidden for this command, but needs to exist.
    parser.add_argument(
        '--plain',
        action='store_true',
        help=argparse.SUPPRESS)

    user_host = parser.add_argument(
        'user_host',
        completion_resource='compute.instances',
        help='Specifies the user/instance for the serial port connection',
        metavar='[USER@]INSTANCE')
    user_host.detailed_help = """\
        Specifies the user/instance for the serial port connection.

        ``USER'' specifies the username to authenticate as. If omitted,
        the current OS user is selected.
        """

    port = parser.add_argument(
        '--port',
        help=('The number of the requested serial port. '
              'Can be 1-4, default is 1.'),
        type=arg_parsers.BoundedInt(1, 4))
    port.detailed_help = """\
        The number of the requested serial port. Can be 1-4, default is 1.

        Instances can support up to four serial ports. By default, this
        command will connect to the first serial port. Setting this flag
        will connect to the requested serial port.
        """

    extra_args = parser.add_argument(
        '--extra-args',
        help=('Extra key-value pairs to pass to the connection.'),
        type=arg_parsers.ArgDict(min_length=1),
        default={},
        metavar='KEY=VALUE')
    extra_args.detailed_help = """\
        Optional arguments can be passed to the serial port connection by
        passing key-value pairs to this flag, such as max-connections=N or
        replay-lines=N. See {0} for additional options.
        """.format(SERIAL_PORT_HELP)

    parser.add_argument(
        '--serial-port-gateway',
        help=argparse.SUPPRESS,
        default=SERIAL_PORT_GATEWAY)

    flags.AddZoneFlag(
        parser,
        resource_type='instance',
        operation_type='connect to')

  def Run(self, args):
    super(ConnectToSerialPort, self).Run(args)

    parts = args.user_host.split('@')
    if len(parts) == 1:
      user = getpass.getuser()
      instance = parts[0]
    elif len(parts) == 2:
      user, instance = parts
    else:
      raise exceptions.ToolException(
          'Expected argument of the form [USER@]INSTANCE; received [{0}].'
          .format(args.user_host))

    # Update google_compute_known_hosts file with published host key
    if args.serial_port_gateway == SERIAL_PORT_GATEWAY:
      http_client = http.Http()
      http_response = http_client.request(HOST_KEY_URL)
      hostname = '[{0}]:{1}'.format(SERIAL_PORT_GATEWAY, CONNECTION_PORT)
      known_hosts = ssh.KnownHosts.FromDefaultFile()
      if http_response[0]['status'] == '200':
        host_key = http_response[1].strip()
        known_hosts.Add(hostname, host_key, overwrite=True)
        known_hosts.Write()
      elif known_hosts.ContainsAlias(hostname):
        log.warn('Unable to download and update Host Key for [{0}] from [{1}]. '
                 'Attempting to connect using existing Host Key in [{2}]. If '
                 'the connection fails, please try again to update the Host '
                 'Key.'.format(SERIAL_PORT_GATEWAY, HOST_KEY_URL,
                               known_hosts.file_path))
      else:
        known_hosts.Add(hostname, DEFAULT_HOST_KEY)
        known_hosts.Write()
        log.warn('Unable to download Host Key for [{0}] from [{1}]. To ensure '
                 'the security of the SSH connetion, gcloud will attempt to '
                 'connect using a hard-coded Host Key value. If the connection '
                 'fails, please try again. If the problem persists, try '
                 'updating gcloud and connecting again.'
                 .format(SERIAL_PORT_GATEWAY, HOST_KEY_URL))

    instance_ref = instance_flags.SSH_INSTANCE_RESOLVER.ResolveResources(
        [instance], compute_scope.ScopeEnum.ZONE, args.zone, self.resources,
        scope_lister=flags.GetDefaultScopeLister(
            self.compute_client, self.project))[0]
    instance = self.GetInstance(instance_ref)

    ssh_args = [self.env.ssh]

    ssh_args.extend(ssh.GetDefaultFlags(self.keys.key_file))
    if args.serial_port_gateway == SERIAL_PORT_GATEWAY:
      ssh_args.extend(['-o', 'StrictHostKeyChecking=yes'])

    ssh_args.extend(['-p', CONNECTION_PORT])

    if args.port:
      port = 'port={0}'.format(args.port)
    else:
      port = 'port=1'

    constructed_username_list = [instance_ref.project, instance_ref.zone,
                                 instance_ref.Name(), user, port]

    if args.extra_args:
      for k, v in args.extra_args.items():
        constructed_username_list.append('{0}={1}'.format(k, v))

    ssh_args.append(ssh.UserHost('.'.join(constructed_username_list),
                                 args.serial_port_gateway))

    log.info('ssh command: {0}'.format(' '.join(ssh_args)))

    # Don't wait for the instance to become SSHable. We are not connecting to
    # the instance itself through SSH, so the instance doesn't need to have
    # fully booted to connect to the serial port. Also, ignore exit code 255,
    # since the normal way to terminate the serial port connection is ~. and
    # that causes ssh to exit with 255.
    return_code = self.ActuallyRun(
        args, ssh_args, user, instance, instance_ref.project,
        strict_error_checking=False, use_account_service=False,
        wait_for_sshable=False, ignore_ssh_errors=True)
    if return_code:
      sys.exit(return_code)


ConnectToSerialPort.detailed_help = {
    'brief': 'Connect to the serial port of an instance.',
    'DESCRIPTION': """\
      *{command}* allows users to connect to, and interact with, a VM's
      virtual serial port using ssh as the secure, authenticated transport
      protocol.

      The user must first enable serial port access to a given VM by setting
      the 'serial-port-enable=true' metadata key-value pair. Setting
      'serial-port-enable' on the project-level metadata enables serial port
      access to all VMs in the project.

      This command uses the same SSH key pair as the `gcloud compute ssh`
      command and also ensures that the user's public SSH key is present in
      the project's metadata. If the user does not have a public SSH key,
      one is generated using ssh-keygen.
      """,
    }
