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
"""Command for updating Workstations."""

from googlecloudsdk.api_lib.workstations import workstations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.workstations import flags as workstations_flags


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
@base.DefaultUniverseOnly
class Update(base.UpdateCommand):
  """Update a workstation.

  Update a workstation's properties, such as its persistent directory disk size.

  ## EXAMPLES

    To update the persistent directory disk size to 500GB, run:

      $ {command} WORKSTATION --pd-disk-size=500
  """

  @classmethod
  def Args(cls, parser):
    workstations_flags.AddAsyncFlag(parser)
    workstations_flags.AddWorkstationResourceArg(parser)
    workstations_flags.AddWorkstationUpdatePersistentDirectoryFields(parser)

  def Collection(self):
    return 'workstations.projects.locations.workstationClusters.workstationConfigs.workstations'

  def Run(self, args):
    client = workstations.Workstations(self.ReleaseTrack())
    return client.Update(args)
