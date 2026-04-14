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

from googlecloudsdk.api_lib.workloadidentity import service_agents
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

  `{command} ` generates
  service agents for a given service producer in a specific project, folder, or
  organization and
  location.

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

    if args.project:
      parent = f'projects/{args.project}/locations/{location}/serviceProducers/{service}'
    elif args.folder:
      parent = f'folders/{args.folder}/locations/{location}/serviceProducers/{service}'
    elif args.organization:
      parent = f'organizations/{args.organization}/locations/{location}/serviceProducers/{service}'
    else:
      # This should not be reachable due to the required
      # mutually exclusive group.
      raise exceptions.Error(
          'Must specify one of --project, --folder, or --organization.'
      )

    op = service_agents.GenerateServiceAgents(parent, self.ReleaseTrack())

    if not op:
      raise exceptions.Error(
          'Service agents generation did not complete successfully.'
      )
    else:
      if args.project:
        log.status.Print(
            f'Service agents generating for {service} in {location} '
            f'under project {args.project}.'
        )
      elif args.folder:
        log.status.Print(
            f'Service agents generating for {service} in {location} '
            f'under folder {args.folder}.'
        )
      elif args.organization:
        log.status.Print(
            f'Service agents generating for {service} in {location} '
            f'under organization {args.organization}.'
        )
      return op
