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
"""List Google Compute Engine Organization Rollouts."""

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.UniverseCompatible
class List(base.ListCommand):
  """List Google Compute Engine Organization Rollouts."""

  detailed_help = {
      'brief': 'List Google Compute Engine Organization Rollouts.',
      'DESCRIPTION': (
          'List Google Compute Engine Organization Rollouts in an organization.'
      ),
      'EXAMPLES': (
          r"""
    To list all organization rollouts in organization '123456789', run:

      $ {command} --organization=123456789
    """
      ),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--organization',
        required=True,
        help='The Google Cloud organization ID.',
    )
    parser.display_info.AddFormat("""
      table(
        name,
        id,
        creationTimestamp:label=CREATION_TIME,
        locationScope:label=LOCATION_SCOPE,
        status,
        description
      )
    """)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    service = client.apitools_client.organizationRollouts
    messages = holder.client.messages

    request = messages.ComputeOrganizationRolloutsListRequest(
        organization='organizations/' + args.organization,
    )

    return list_pager.YieldFromList(
        service,
        request,
        limit=args.limit,
        batch_size=args.page_size,
        method='List',
        field='items',
        current_token_attribute='pageToken',
        next_token_attribute='nextPageToken',
        batch_size_attribute='maxResults',
    )
