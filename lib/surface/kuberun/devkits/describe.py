# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command to describe a Kuberun Development Kit."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import kuberun_command
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To show all the data about a Development Kit, run:

            $ {command}
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(kuberun_command.KubeRunCommandWithOutput, base.DescribeCommand):
  """Describe a Development Kit."""

  detailed_help = _DETAILED_HELP
  flags = []

  @classmethod
  def Args(cls, parser):
    super(Describe, cls).Args(parser)
    parser.add_argument(
        'devkit', help='The Development Kit to show details for.')

  def Command(self):
    return ['devkits', 'describe']

  def BuildKubeRunArgs(self, args):
    return [args.devkit] + super(Describe, self).BuildKubeRunArgs(args)

  def FormatOutput(self, out, args):
    # TODO(b/169186627): handle this as JSON
    if not out:
      return out
    return out + '\n'

  # TODO(b/169186627): remove this workaround
  def Display(self, args, output):
    log.out.write(output)
