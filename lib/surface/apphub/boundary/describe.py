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
"""gcloud apphub boundary describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.apphub import boundary as boundary_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apphub import flags


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.GA)
class DescribeGA(base.DescribeCommand):
  """Show metadata for an App Hub boundary."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddDescribeBoundaryFlags(parser)

  def Run(self, args):
    """Run the describe command."""
    client = boundary_api.BoundaryClient(self.ReleaseTrack())
    # Parse the location reference from the --location flag
    location_ref = args.CONCEPTS.location.Parse()
    # Manually construct the full boundary resource name string
    boundary_name = location_ref.RelativeName() + '/boundary'
    return client.Describe(boundary_name)


@base.DefaultUniverseOnly
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(base.DescribeCommand):
  """Show metadata for an App Hub boundary."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddDescribeBoundaryFlags(parser)

  def Run(self, args):
    """Run the describe command."""
    client = boundary_api.BoundaryClient(self.ReleaseTrack())
    # Parse the location reference from the --location flag
    location_ref = args.CONCEPTS.location.Parse()
    # Manually construct the full boundary resource name string
    boundary_name = location_ref.RelativeName() + '/boundary'
    return client.Describe(boundary_name)
