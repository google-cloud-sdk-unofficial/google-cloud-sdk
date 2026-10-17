# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command to create a new Assured Workloads environment."""

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.base import ReleaseTrack
from googlecloudsdk.command_lib.assured import create_workload
from googlecloudsdk.command_lib.assured import flags


class _CreateWorkloadBase(object):
  """Create a new Assured Workloads environment."""

  detailed_help = create_workload.DETAILED_HELP

  def Run(self, args):
    """Run the create command, routing to V1 or V2 based on the --version flag."""
    flags.ValidateCreateWorkloadVersionFlags(args)
    version = flags.GetApiVersion(args, release_track=self.ReleaseTrack())
    if version == 'v2':
      self.created_resource, self.is_async = create_workload.RunV2(
          args, self.ReleaseTrack()
      )
    else:
      self.created_resource = create_workload.RunV1(args, self.ReleaseTrack())
      self.is_async = False
    return self.created_resource

  def Epilog(self, unused_resources_were_displayed):
    """Displays resource creation message upon command completion."""
    create_workload.Epilog(
        getattr(self, 'created_resource', None),
        getattr(self, 'is_async', False),
    )


@base.ReleaseTracks(ReleaseTrack.GA)
class GaCreate(_CreateWorkloadBase, base.CreateCommand):
  """Create a new Assured Workloads environment."""

  @staticmethod
  def Args(parser):
    """Register flags for GA release track."""
    flags.AddUnifiedCreateWorkloadFlags(parser, ReleaseTrack.GA)


@base.ReleaseTracks(ReleaseTrack.BETA)
class BetaCreate(_CreateWorkloadBase, base.CreateCommand):
  """Create a new Assured Workloads environment."""

  @staticmethod
  def Args(parser):
    """Register flags for Beta release track."""
    flags.AddUnifiedCreateWorkloadFlags(parser, ReleaseTrack.BETA)


@base.ReleaseTracks(ReleaseTrack.ALPHA)
class AlphaCreate(_CreateWorkloadBase, base.CreateCommand):
  """Create a new Assured Workloads environment."""

  @staticmethod
  def Args(parser):
    """Register flags for Alpha release track."""
    flags.AddUnifiedCreateWorkloadFlags(parser, ReleaseTrack.ALPHA)
