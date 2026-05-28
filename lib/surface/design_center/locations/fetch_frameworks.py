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
"""Command to fetch frameworks for a location."""


from googlecloudsdk.api_lib.design_center import locations as apis
from googlecloudsdk.api_lib.design_center import utils as api_lib_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.design_center import flags

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To fetch frameworks for a specific design center location `us-central1` in project `my-project`, run:

          $ {command} us-central1 --project=my-project

        To fetch frameworks for a specific design center location using multiple project IDs, run:

          $ {command} us-central1 --project=my-project --projects=project1,project2
        """,
}


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.UniverseCompatible
class FetchFrameworksGA(base.Command):
  """Fetch frameworks available for assessment."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddDescribeLocationFlags(parser)
    parser.add_argument(
        '--projects',
        metavar='PROJECTS',
        type=arg_parsers.ArgList(),
        help=('The list of projects to fetch frameworks for. Each entry can be '
              'a simple project ID or the full resource name '
              'projects/my-project. '
              'Note that this is separate from the global --project flag which '
              'identifies the project owning the Design Center resource.'))

  def Run(self, args):
    """Run the fetch-frameworks command."""
    client = apis.LocationsClient(release_track=base.ReleaseTrack.GA)
    location_ref = api_lib_utils.GetLocationRef(args)
    projects = args.projects or []
    return client.FetchFrameworks(
        parent=location_ref.RelativeName(),
        projects=projects)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class FetchFrameworksAlpha(base.Command):
  """Fetch frameworks available for assessment."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddDescribeLocationFlags(parser)
    parser.add_argument(
        '--projects',
        metavar='PROJECTS',
        type=arg_parsers.ArgList(),
        help=('The list of projects to fetch frameworks for. Each entry can be '
              'a simple project ID or the full resource name '
              'projects/my-project. '
              'Note that this is separate from the global --project flag which '
              'identifies the project owning the Design Center resource.'))

  def Run(self, args):
    """Run the fetch-frameworks command."""
    client = apis.LocationsClient(release_track=base.ReleaseTrack.ALPHA)
    location_ref = api_lib_utils.GetLocationRef(args)
    projects = args.projects or []
    return client.FetchFrameworks(
        parent=location_ref.RelativeName(),
        projects=projects)
