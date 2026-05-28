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
"""Command to upgrade Cluster Upgrades in a Rollout Sequence."""

from __future__ import annotations

from apitools.base.py import encoding
from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.rolloutsequences import flags as rolloutsequence_flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console.style import text
from googlecloudsdk.generated_clients.apis.gkehub.v1alpha import gkehub_v1alpha_messages as alpha_messages


@base.DefaultUniverseOnly
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Upgrade(base.Command):
  """Upgrade the clusters in a rollout sequence resource."""

  _release_track = base.ReleaseTrack.ALPHA

  @classmethod
  def Args(cls, parser: parser_arguments.ArgumentInterceptor):
    """Registers flags for this command."""
    flags = rolloutsequence_flags.RolloutSequenceFlags(
        parser, release_track=cls._release_track
    )
    flags.AddRolloutSequenceResourceArg()
    flags.AddUpgradeFlags()
    flags.AddAsync()

  def Run(self, args: parser_extensions.Namespace) -> alpha_messages.Operation:
    """Runs the upgrade command."""
    fleet_client = client.FleetClient(release_track=self.ReleaseTrack())
    flag_parser = rolloutsequence_flags.RolloutSequenceFlagParser(
        args, release_track=self.ReleaseTrack()
    )

    req = fleet_client.messages.GkehubProjectsLocationsRolloutSequencesUpgradeRequest(
        name=resources.RolloutSequenceResourceName(args),
        upgradeRolloutSequenceRequest=fleet_client.messages.UpgradeRolloutSequenceRequest(
            upgradeType=flag_parser.UpgradeType(),
            version=flag_parser.Version(),
        ),
    )
    operation = fleet_client.UpgradeRolloutSequence(req)

    rolloutsequence_ref = util.RolloutSequenceRef(args)
    if flag_parser.Async():
      log.status.Print(
          'Upgrade request issued for rollout sequence:',
          text.TextTypes.RESOURCE_NAME(rolloutsequence_ref.Name()) + '.',
      )
      log.status.Print(
          'Check operation',
          text.TextTypes.RESOURCE_NAME(operation.name),
          'for status.',
      )
      return None

    operation_client = client.OperationClient(release_track=self.ReleaseTrack())
    completed_operation = operation_client.Wait(util.OperationRef(operation))

    if completed_operation:
      response_dict = encoding.MessageToPyValue(completed_operation)
      full_rollout_name = response_dict.get('rollout', '')
      rollout_id = full_rollout_name.split('/')[-1] if full_rollout_name else ''
    else:
      rollout_id = ''

    sequence_id = rolloutsequence_ref.Name()
    if rollout_id:
      log.status.Print(
          'Rollout',
          rollout_id,
          'created for rollout sequence:',
          text.TextTypes.RESOURCE_NAME(sequence_id) + '.',
      )
    else:
      log.warning(
          'Rollout created for rollout sequence %s, but the'
          ' rollout name is missing from the API response.',
          sequence_id,
      )
    return None
