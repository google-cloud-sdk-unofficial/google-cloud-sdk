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
"""Command for suspending Workstations."""

from googlecloudsdk.api_lib.workstations import workstations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.workstations import flags as workstations_flags


@base.UniverseCompatible
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Suspend(base.Command):
  """Suspend a workstation to reduce costs.

  Suspend a workstation to reduce costs. This keeps the assignment to the
  existing VM but suspends it, rather than stopping the workstation which
  unassigns the VM.

  ## EXAMPLES

    To suspend a workstation, run:

      $ {command} WORKSTATION
  """

  @staticmethod
  def Args(parser):
    workstations_flags.AddAsyncFlag(parser)
    workstations_flags.AddWorkstationResourceArg(parser)

  def Collection(self):
    return 'workstations.projects.locations.workstationClusters.workstationConfigs.workstations'

  def Run(self, args):
    client = workstations.Workstations(self.ReleaseTrack())
    response = client.Suspend(args)
    return response
