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
"""Command to describe an App Topology location."""

from googlecloudsdk.api_lib.app_topology import locations as locations_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app_topology import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Describe(base.DescribeCommand):
  """Describe an App Topology location.

  Retrieves and displays details and supported capabilities for a specific
  location.
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES': (
          """\
          To describe the `global` location:

            $ {command} global
          """
      ),
  }

  @staticmethod
  def Args(parser):
    """Registers command-line flags and arguments for locations describe."""
    concept_parsers.ConceptParser.ForResource(
        'LOCATION',
        resource_args.GetLocationResourceSpec(),
        'The location to describe.',
        required=True,
    ).AddToParser(parser)

  def Run(self, args):
    """Executes the locations describe command.

    Args:
      args: argparse.Namespace, The parsed command-line arguments.

    Returns:
      messages.Location: The location metadata message.
    """
    client = locations_api.LocationsClient()
    location_ref = args.CONCEPTS.location.Parse()
    return client.Get(name=location_ref.RelativeName())
