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

"""Implements the command for copying files from and to virtual machines."""

from googlecloudsdk.command_lib.compute import scp_utils


class Scp(scp_utils.BaseScpCommand):
  """Copy files to and from Google Compute Engine virtual machines."""

  @staticmethod
  def Args(parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    super(Scp, Scp).Args(parser)

    parser.add_argument(
        '--port',
        help='The port to connect to.')

    parser.add_argument(
        '--recurse',
        action='store_true',
        help='Upload directories recursively.')

    parser.add_argument(
        '--compress',
        action='store_true',
        help='Enable compression.')

    parser.add_argument(
        '--scp-flag',
        action='append',
        help='Extra flag to be sent to scp. This flag may be repeated.')

  def Run(self, args):
    """See scp_utils.BaseScpCommand.Run."""
    extra_flags = []
    # TODO(b/33467618): Add -C to SCPCommand
    if args.scp_flag:
      extra_flags.extend(args.scp_flag)
    return super(Scp, self).Run(args, port=args.port, recursive=args.recurse,
                                compress=args.compress, extra_flags=extra_flags)
