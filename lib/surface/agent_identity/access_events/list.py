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

"""Command to list access events."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class List(base.ListCommand):
  r"""List accessEvents.

  List accessEvents for a given location and filter.

  ## EXAMPLES

  To list access events for a workload, run:

      $ {command} --location=us-central1 --filter='workload_id="my-workload"' \
          --project="my-project"
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        '--location', required=True, help='Location to list access events for.'
    )
    parser.display_info.AddFormat('table(name)')

  def Run(self, args):
    project = properties.VALUES.core.project.GetOrFail()

    # Parse the location flag safely to support both short names and fully
    # qualified resource names.
    location_ref = resources.REGISTRY.Parse(
        args.location,
        params={'projectsId': project},
        collection='iamconnectors.projects.locations',
    )

    parent = location_ref.RelativeName()

    client = apis.GetClientInstance('iamconnectors', 'v1alpha')
    messages = client.MESSAGES_MODULE

    # Re-route standard gcloud filter to server-side filter to support the
    # required workload_id filter on the server.
    server_filter = getattr(args, 'filter', None)

    # Clear args.filter to prevent the client-side framework from applying
    # local evaluation which breaks on workload_id="str".
    args.filter = None

    request = messages.IamconnectorsProjectsLocationsAccessEventsListRequest(
        parent=parent,
        filter=server_filter,
        pageSize=args.page_size,
    )

    return list_pager.YieldFromList(
        client.projects_locations_accessEvents,
        request,
        field='accessEvents',
        limit=args.limit,
        batch_size_attribute='pageSize',
        batch_size=args.page_size,
    )
