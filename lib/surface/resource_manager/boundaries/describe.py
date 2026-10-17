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
"""Command to describe a boundary."""

from googlecloudsdk.api_lib.resource_manager import boundaries
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager.boundaries import resource_args


@base.Hidden
@base.DefaultUniverseOnly
@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Describe(base.DescribeCommand):
  """Describe a boundary.

  `{command}` describes a boundary given its ID and parent or its full resource
  name.

  ## EXAMPLES

  To describe a boundary with ID `my-boundary` in an organization with ID
  `123456789012`, run:

    $ {command} my-boundary --organization=123456789012

  To describe a boundary by full resource name, run:

    $ {command} organizations/123456789012/boundaries/my-boundary
  """

  @staticmethod
  def Args(parser):
    resource_args.AddBoundaryResourceArgToParser(parser, 'to describe')

  def Run(self, args):
    resource_ref = resource_args.ParseBoundary(args)
    name = resource_ref.RelativeName()
    return boundaries.GetBoundary(name)
