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
"""Describes a Cloud NetApp Volumes Inventory."""

from googlecloudsdk.api_lib.netapp import util as netapp_api_util
from googlecloudsdk.api_lib.netapp.inventory import client as inventory_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


@base.RegionalEndpointsSupported
@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.Hidden
class Describe(base.DescribeCommand):
  """Describe a Cloud NetApp Volumes Inventory."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION': (
          """\
          Describe a Cloud NetApp Volumes Inventory in a given location.
          """
      ),
      'EXAMPLES': (
          """\
          The following command describes an Inventory in the location us-central1:

              $ {command} --location=us-central1
          """
      ),
  }

  @classmethod
  def Args(cls, parser):
    concept_parsers.ConceptParser([
        presentation_specs.ResourcePresentationSpec(
            '--location',
            flags.GetLocationResourceSpec(),
            'The location to describe the inventory.',
            required=True,
        )
    ]).AddToParser(parser)

    messages = netapp_api_util.GetMessagesModule(
        release_track=cls._RELEASE_TRACK
    )
    flags.GetInventoryViewArg(messages).choice_arg.AddToParser(parser)

  def Run(self, args):
    """Run the describe command."""
    location_ref = args.CONCEPTS.location.Parse()
    client = inventory_client.InventoryClient(release_track=self._RELEASE_TRACK)
    inventory_view = None
    if args.view is not None:
      inventory_view = flags.GetInventoryViewArg(
          client.messages
      ).GetEnumForChoice(args.view)
    return client.Get(location_ref, inventory_view)


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class DescribeAlpha(Describe):
  """Describe a Cloud NetApp Volumes Inventory."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA
