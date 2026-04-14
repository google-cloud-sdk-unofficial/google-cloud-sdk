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
"""Command to generate service agents for Workload Identity."""

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.api_lib.workloadidentity import service_agents
from googlecloudsdk.api_lib.workloadidentity import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
@base.UniverseCompatible
class Generate(base.CreateCommand):
  """Generate service agents for a service producer.

  It can be generated in a project, folder, or organization and location.

  `{command}` generates service agents for a given service producer in a
  specific project, folder, or organization and location.

  ## EXAMPLES

  To generate service agents for `bigquery.googleapis.com` in the `global`
  location for the project `123456`, run:

    $ {command} --service="bigquery.googleapis.com" --location="global"
    --project="123456"

  To generate service agents for `bigquery.googleapis.com` in the `global`
  location for the folder `123456`, run:

    $ {command} --service="bigquery.googleapis.com" --location="global"
    --folder="123456"

  To generate service agents for `bigquery.googleapis.com` in the `global`
  location for the organization `123456`, run:

    $ {command} --service="bigquery.googleapis.com" --location="global"
    --organization="123456"
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        '--service',
        required=True,
        help=(
            'The service producer to generate service agents for (e.g.'
            ' bigquery.googleapis.com).'
        ),
    )

    parser.add_argument(
        '--location',
        required=False,
        default='global',
        help=(
            'The location for which to generate the service agents. Defaults to'
            ' global.'
        ),
    )

    scope_group = parser.add_mutually_exclusive_group(required=True)
    scope_group.add_argument(
        '--project',
        help='The project number to generate service agents for.',
    )
    scope_group.add_argument(
        '--folder',
        help='The folder number to generate service agents for.',
    )
    scope_group.add_argument(
        '--organization',
        help='The organization number to generate service agents for.',
    )

  def Run(self, args):
    """Run the generating command."""
    location = args.location
    service = args.service
    scope_type = None
    scope_id = None

    if args.project:
      scope_type = 'projects'
      scope_id = args.project
    elif args.folder:
      scope_type = 'folders'
      scope_id = args.folder
    elif args.organization:
      scope_type = 'organizations'
      scope_id = args.organization
    # No else is needed here because the argument group is required.

    container = f'{scope_type}/{scope_id}'
    parent = f'{container}/locations/{location}/serviceProducers/{service}'
    msg = (
        f'Generating service agents for {service} in {location} '
        f'under {container}'
    )

    op = service_agents.GenerateServiceAgents(parent, self.ReleaseTrack())

    if not op:
      raise exceptions.Error(
          'Service agents generation did not complete successfully.'
      )

    client = api_util.GetClientInstance(self.ReleaseTrack())
    poller = waiter.CloudOperationPollerNoResources(
        client.projects_locations_operations, get_name_func=lambda x: x
    )
    result = waiter.WaitFor(poller, op.name, msg)
    response_dict = encoding.MessageToPyValue(result) if result else {}
    service_agents_list = response_dict.get('serviceAgents', [])

    log.status.Print(
        f'\nProvisioned service agents for {service} under {container}:\n'
    )
    for sa_dict in service_agents_list:
      for key, value in sa_dict.items():
        log.status.Print(f'{key}: {value}')
      log.status.Print('----')

    return result
