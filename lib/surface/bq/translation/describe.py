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
"""Implements command to describe a batch translation."""

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bq import translation_utils as utils
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.UniverseCompatible
class Describe(base.DescribeCommand):
  """Get the details or status of a submitted batch translation.

  ## EXAMPLES

  To get the details of a batch translation with ID
  `12345678-1234-1234-1234-1234567890ab` in location `us-central1`, run:

    $ {command} 12345678-1234-1234-1234-1234567890ab --location=us-central1
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'translation_id',
        metavar='TRANSLATION_ID',
        help='The translation ID to describe.',
    )
    parser.add_argument(
        '--location',
        required=True,
        help='The location of the translation.',
    )

  def Run(self, args):
    client = utils.get_migration_client()
    migration_service = client.projects_locations_workflows

    project = properties.VALUES.core.project.Get(required=True)
    location = args.location
    translation_id = args.translation_id

    workflow_ref = resources.REGISTRY.Parse(
        translation_id,
        params={
            'projectsId': project,
            'locationsId': location,
        },
        collection='bigquerymigration.projects.locations.workflows',
    )

    messages = client.MESSAGES_MODULE
    request = messages.BigquerymigrationProjectsLocationsWorkflowsGetRequest(
        name=workflow_ref.RelativeName(),
    )

    response = migration_service.Get(request)
    return response
