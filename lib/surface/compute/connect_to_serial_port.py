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

from googlecloudsdk.api_lib.compute import ssh_utils
from googlecloudsdk.api_lib.compute import utils

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log

SERIAL_PORT_GATEWAY = 'ssh-serialport.googleapis.com'
CONNECTION_PORT = '9600'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ConnectToSerialPort(ssh_utils.BaseSSHCLICommand):
  """Class for connecting through a gateway to the interactive serial port."""

  @staticmethod
  def Args(parser):
    ssh_utils.BaseSSHCLICommand.Args(parser)

    user_host = parser.add_argument(
        'user_host',
        completion_resource='compute.instances',
        help='Specifies the user/instance for the serial port connection',
        metavar='[USER@]INSTANCE')
    user_host.detailed_help = """\
        Specifies the user/instance to for the serial port connection.

        ``USER'' specifies the username to authenticate as. If omitted,
        the current OS user is selected.
        """

    port = parser.add_argument(
        '--port',
        help=('The number of the requested serial port. '
              'Can be 1-4, default is 1.'),
        type=arg_parsers.BoundedInt(1, 4))
    port.detailed_help = """\
        Instances can support up to four serial ports. By default, this
        command will connect to the first serial port. Setting this flag
        will connect to the requested serial port.
        """

    extra_args = parser.add_argument(
        '--extra-args',
        help=('Extra key-value pairs to pass to the connection.'),
        type=arg_parsers.ArgDict(min_length=1),
        action=arg_parsers.FloatingListValuesCatcher(),
        default={},
        metavar='KEY=VALUE')
    extra_args.detailed_help = """\
        Optional arguments can be passed to the serial port connection by
        passing key-value pairs to this flag.
        """

    parser.add_argument(
        '--serial-port-gateway',
        help=argparse.SUPPRESS,
        default=SERIAL_PORT_GATEWAY)

    utils.AddZoneFlag(
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

    instance_ref = self.CreateZonalReference(instance, args.zone)
    instance = self.GetInstance(instance_ref)

    ssh_args = [self.ssh_executable]

    ssh_args.extend(['-i', self.ssh_key_file])
    ssh_args.extend(['-o', 'IdentitiesOnly=yes'])
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

    ssh_args.append(ssh_utils.UserHost('.'.join(constructed_username_list),
                                       args.serial_port_gateway))

    log.info('ssh command: {0}'.format(' '.join(ssh_args)))

    # Don't wait for the instance to become SSHable. We are not connecting to
    # the instance itself through SSH, so the instance doesn't need to have
    # fully booted to connect to the serial port.
    return_code = self.ActuallyRun(
        args, ssh_args, user, instance,
        strict_error_checking=False, use_account_service=False,
        wait_for_sshable=False)
    if return_code:
      sys.exit(return_code)


ConnectToSerialPort.detailed_help = {
    'brief': 'Connect to the serial port of an instance.',
    'DESCRIPTION': """\
      *{command}* is a helper command to connect through SSH to the serial
      console of an instance. It supports connections to up to four serial
      ports on the instance.

      This command creates an SSH connection to a Google gateway that connects
      to the serial port of the instance. Authentication is done using the
      same project SSH keys used by the ``gcloud compute ssh'' command.
      """,
    }

