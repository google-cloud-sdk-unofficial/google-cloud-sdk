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
"""Command to force-complete a rollout stage."""

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.api_lib.container.fleet import types
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.container.fleet.rollouts import flags as rollout_flags
from googlecloudsdk.core import log


_EXAMPLES = """
To force-complete stage 1 of a rollout, run:

$ {command} ROLLOUT --stage=1
"""


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class ForceCompleteStage(base.UpdateCommand):
  """Force-complete a rollout stage."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @classmethod
  def Args(cls, parser: parser_arguments.ArgumentInterceptor):
    """Registers flags for the force-complete-stage command."""
    flags = rollout_flags.RolloutFlags(parser, cls.ReleaseTrack())
    flags.AddRolloutResourceArg()
    flags.AddAsync()
    flags.AddStage()

  def Run(self, args: parser_extensions.Namespace) -> types.Operation:
    """Runs the force-complete-stage command."""
    flag_parser = rollout_flags.RolloutFlagParser(
        args, release_track=self.ReleaseTrack()
    )
    fleet_client = client.FleetClient(release_track=self.ReleaseTrack())
    req = fleet_client.messages.GkehubProjectsLocationsRolloutsForceCompleteStageRequest(
        name=util.RolloutName(args),
        forceCompleteRolloutStageRequest=fleet_client.messages.ForceCompleteRolloutStageRequest(
            stageNumber=args.stage,
        ),
    )

    operation = fleet_client.ForceCompleteRolloutStage(req)
    rollout_ref = util.RolloutRef(args)

    if flag_parser.Async():
      log.status.Print(
          'Force-completing stage [{}] in progress for rollout [{}]'.format(
              args.stage,
              rollout_ref.SelfLink()
          )
      )
      return operation

    operation_client = client.OperationClient(
        release_track=self.ReleaseTrack()
    )
    completed_operation = operation_client.Wait(util.OperationRef(operation))
    log.status.Print(
        'Force-completed stage [{}] for rollout [{}].'.format(
            args.stage,
            rollout_ref.SelfLink()
        )
    )

    return completed_operation
