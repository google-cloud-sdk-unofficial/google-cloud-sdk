# -*- coding: utf-8 -*- #
# Copyright 2025 Google LLC. All Rights Reserved.
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
"""Command to create a rollout sequence."""

from __future__ import annotations
from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.api_lib.container.fleet import types
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.container.fleet.rolloutsequences import flags as rolloutsequence_flags
from googlecloudsdk.core import log


_EXAMPLES = """
To create a rollout sequence, run:

$ {command} ROLLOUTSEQUENCE --stage-config=path/to/config.yaml
"""


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Create(base.CreateCommand):
  """Create a rollout sequence resource."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @classmethod
  def Args(cls, parser: parser_arguments.ArgumentInterceptor):
    """Registers flags for this command."""
    flags = rolloutsequence_flags.RolloutSequenceFlags(
        parser, release_track=cls.ReleaseTrack()
    )
    flags.AddRolloutSequenceResourceArg()
    flags.AddDisplayName()
    flags.AddLabels()
    flags.AddStageConfig(required=True)
    flags.AddIgnoredClustersSelectorFlags()
    flags.AddAutoRolloutScope()
    flags.AddAsync()

  def Run(
      self, args: parser_extensions.Namespace
  ) -> types.Operation:
    """Runs the create command."""
    flag_parser = rolloutsequence_flags.RolloutSequenceFlagParser(
        args, release_track=self.ReleaseTrack()
    )
    fleet_client = client.FleetClient(release_track=self.ReleaseTrack())
    req = fleet_client.messages.GkehubProjectsLocationsRolloutSequencesCreateRequest(
        parent=util.RolloutSequenceParentName(args),
        rolloutSequence=flag_parser.RolloutSequence(),
        rolloutSequenceId=util.RolloutSequenceId(args),
    )
    operation = fleet_client.CreateRolloutSequence(req)
    rolloutsequence_ref = util.RolloutSequenceRef(args)

    if flag_parser.Async():
      log.CreatedResource(
          rolloutsequence_ref,
          kind='Rollout sequence',
          is_async=flag_parser.Async()
      )
      return operation

    operation_client = client.OperationClient(
        release_track=self.ReleaseTrack()
    )
    completed_operation = operation_client.Wait(util.OperationRef(operation))
    log.CreatedResource(rolloutsequence_ref, kind='Rollout sequence')
    return completed_operation
