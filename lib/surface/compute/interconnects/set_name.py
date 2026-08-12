# -*- coding: utf-8 -*- #
# Copyright 2026 Google LLC. All Rights Reserved.
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
"""Command for renaming interconnects."""


from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.interconnects import client as api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.interconnects import flags


@base.UniverseCompatible
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA,
)
class InterconnectSetName(base.SilentCommand):
  """Set name for a Compute Engine interconnect."""

  @staticmethod
  def Args(parser):
    flags.InterconnectArgument().AddArgument(parser, operation_type='set-name')

    parser.add_argument(
        '--new-name',
        required=True,
        help='Specifies the new name of the interconnect.')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())

    interconnect_ref = flags.InterconnectArgument().ResolveAsResource(
        args, holder.resources)

    interconnect = api_client.Interconnect(
        interconnect_ref, compute_client=holder.client
    )

    obj = interconnect.Describe()

    if args.new_name == obj.name:
      return obj

    return interconnect.SetName(args.new_name)


InterconnectSetName.detailed_help = {
    'brief': 'Set the name of a Compute Engine interconnect.',
    'DESCRIPTION': """
        ``{command}'' lets you change the name of an interconnect.
        """,
    'EXAMPLES': """
        To change the name of ``interconnect-1'' to ``interconnect-2'':

          $ {command} interconnect-1 --new-name=interconnect-2
        """,
}
