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

"""Subscribes a Cloud NetApp Trial."""

from googlecloudsdk.api_lib.netapp.trials import client as trials_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.netapp import util as command_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.Hidden
class Subscribe(base.Command):
  """Subscribe to a Cloud NetApp Trial."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION': (
          """\
          Subscribe to a Cloud NetApp Trial.
          """
      ),
      'EXAMPLES': (
          """\
          The following command subscribes to a Trial:

              $ {command} --location=us-central1
          """
      ),
  }

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser([
        presentation_specs.ResourcePresentationSpec(
            '--location',
            flags.GetLocationResourceSpec(),
            'The location to subscribe to the trial. If not specified, '
            'an available location will be automatically selected.',
            required=False,
        )
    ]).AddToParser(parser)
    flags.AddResourceAsyncFlag(parser)

  def Run(self, args):
    """Run the subscribe command."""
    location_ref = command_util.ParseLocationForTrials(
        args, self._RELEASE_TRACK
    )

    client = trials_client.TrialsClient(release_track=self._RELEASE_TRACK)
    result = client.Subscribe(location_ref, args.async_)
    if args.async_:
      log.status.Print('Subscription in progress.')
    return result


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class SubscribeAlpha(Subscribe):
  """Subscribe to a Cloud NetApp Trial."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA
