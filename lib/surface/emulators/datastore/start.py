# Copyright 2015 Google Inc. All Rights Reserved.
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
"""gcloud datastore emulator start command."""

from googlecloudsdk.api_lib.emulators import datastore_util
from googlecloudsdk.api_lib.emulators import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


class Start(base.Command):
  """Start a local datastore emulator.

  This command starts a local datastore emulator.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': """\
          To start a local datastore emulator, run:

            $ {command} --data-dir DATA-DIR
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--host-port',
        required=False,
        type=lambda arg: arg_parsers.HostPort.Parse(arg, ipv6_enabled=True),
        help='The host:port to which the emulator should be bound. Can '
        'take the form of a single address (hostname, IPv4, or IPv6) and port:'
        '\n\n  ADDRESS[:PORT]\n\n'
        'In this format you must enclose IPv6 addresses in square brackets: '
        'e.g.\n\n'
        '  [2001:db8:0:0:0:ff00:42:8329]:8080\n\n')
    parser.add_argument(
        '--store-on-disk',
        default=True,
        action='store_true',
        help='Whether data should be persisted to disk.')
    parser.add_argument(
        '--consistency',
        required=False,
        type=float,
        default=0.9,
        help='Fraction of datastore operations that should succeed.')

  def Run(self, args):
    if not args.host_port:
      args.host_port = arg_parsers.HostPort.Parse(datastore_util.GetHostPort())
    args.host_port.host = args.host_port.host or 'localhost'

    datastore_util.PrepareGCDDataDir(args)
    datastore_process = datastore_util.StartGCDEmulator(args)
    datastore_util.WriteGCDEnvYaml(args)
    util.PrefixOutput(datastore_process, 'datastore')
