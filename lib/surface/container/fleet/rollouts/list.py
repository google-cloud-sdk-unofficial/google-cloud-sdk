# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command to list fleet rollouts."""

from __future__ import annotations

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.api_lib.container.fleet import types
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.container.fleet import flags as fleet_flags
from googlecloudsdk.command_lib.container.fleet import util as fleet_util


_EXAMPLES = """
To list all rollouts, run:

$ {command}
"""


@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class List(base.ListCommand):
  """List all fleet rollouts."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    """Registers flags for this command.

    Args:
      parser: Top level argument group to add new arguments.
    """
    parser.display_info.AddTransforms({
        'active_stage': _TransformActiveStage,
        'rollout_trigger': _TransformTrigger,
        'upgrade_type': _TransformUpgradeType,
    })

  def Run(
      self, args: parser_extensions.Namespace
  ) -> types.RolloutGenerator:
    """Runs the rollout list command.

    Args:

    Args:
      args: Flag arguments received from command line.

    Returns:
      A list of rollouts under the fleet project.
    """
    if '--format' not in args.GetSpecifiedArgNames():
      args.format = fleet_util.ROLLOUT_LIST_FORMAT

    flag_parser = fleet_flags.FleetFlagParser(
        args, release_track=self.ReleaseTrack()
    )
    fleet_client = client.FleetClient(self.ReleaseTrack())

    req = fleet_client.messages.GkehubProjectsLocationsRolloutsListRequest(
        parent=util.LocationResourceName(flag_parser.Project())
    )
    return fleet_client.ListRollouts(
        req, page_size=flag_parser.PageSize(), limit=flag_parser.Limit()
    )


def _TransformActiveStage(stages, undefined='-'):
  """Returns the active stage of a rollout.

  Args:
    stages: list of stages.
    undefined: value to return if active stage cannot be determined.

  Returns:
    Formatted active stage, e.g. "2 (RUNNING)", "Completed", or undefined.
  """
  if not stages:
    return undefined

  sorted_stages = sorted(
      stages,
      key=lambda x: x.get('stageNumber') or 0,
  )

  active_stage = None
  for stage in sorted_stages:
    state = stage.get('state')
    # Check for both string and potential enum integer values.
    # RUNNING=2, SOAKING=3, PAUSED=6 in proto
    if state in ('RUNNING', 'SOAKING', 'PAUSED', 2, 3, 6):
      active_stage = stage
      break

  if active_stage:
    num = active_stage.get('stageNumber')
    state = active_stage.get('state')
    return f'{num} ({state})'

  return undefined


def _TransformTrigger(trigger, undefined='-'):
  """Returns the formatted trigger of a rollout.

  Args:
    trigger: trigger value (string or enum).
    undefined: value to return if trigger is unknown or unspecified.

  Returns:
    Formatted trigger, e.g. "Manual", "Auto", or undefined.
  """
  if not trigger:
    return undefined

  # USER=1, GKE=2, ROLLOUT_TRIGGER_UNSPECIFIED=0 in proto
  if trigger in ('USER', 1):
    return 'User'
  if trigger in ('GKE', 2):
    return 'GKE'

  return undefined


def _TransformUpgradeType(upgrade_type, undefined='-'):
  """Returns the formatted upgrade type of a rollout.

  Args:
    upgrade_type: upgrade type value (string or enum).
    undefined: value to return if upgrade type is unknown or unspecified.

  Returns:
    Formatted upgrade type, e.g. "CONTROL_PLANE", "NODE", or undefined.
  """
  if not upgrade_type:
    return undefined

  # TYPE_CONTROL_PLANE=1, TYPE_NODE_POOL=2, TYPE_CONFIG_SYNC=3 in proto
  if upgrade_type in ('TYPE_CONTROL_PLANE', 1):
    return 'CONTROL_PLANE'
  if upgrade_type in ('TYPE_NODE_POOL', 2):
    return 'NODE'
  if upgrade_type in ('TYPE_CONFIG_SYNC', 3):
    return 'CONFIG_SYNC'

  return upgrade_type
