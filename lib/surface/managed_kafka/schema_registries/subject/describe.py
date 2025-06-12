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
"""Implementation of gcloud managed kafka schema registries subject describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.managed_kafka import arguments
from googlecloudsdk.command_lib.managed_kafka import util

PROJECTS_RESOURCE_PATH = 'projects/'
LOCATIONS_RESOURCE_PATH = 'locations/'
SCHEMA_REGISTRIES_RESOURCE_PATH = 'schemaRegistries/'
SUBJECTS_RESOURCE_PATH = 'subjects/'
CONTEXTS_RESOURCE_PATH = '/contexts/'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Describe(base.UpdateCommand):
  """Describe a subject in a schema registry with all of its fields.

  ## EXAMPLES

   Describe the subject in a schema registry with all of its fields:

    $ {command} --project=PROJECT_ID --location=LOCATION_ID
    --schema_registry=SCHEMA_REGISTRY_ID
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""

    parser.add_argument(
        '--schema_registry',
        type=str,
        required=True,
        help='The schema registry of the subject.',
    )

    parser.add_argument(
        '--context',
        type=str,
        help='The context of the subject.',
    )

    arguments.AddSubjectArgToParser(parser)

  def Run(self, args):
    """Called when the user runs gcloud managed-kafka schema-registries subject describe ...

    Args:
      args: all the arguments that were provided to this command invocation.

    Returns:
      The subject.
    """
    message = apis.GetMessagesModule('managedkafka', 'v1')
    client = apis.GetClientInstance('managedkafka', 'v1')

    project_id = args.project
    location = args.location
    schema_registry_id = args.schema_registry
    subject = args.CONCEPTS.subject.Parse().subjectsId
    name = '{}{}/{}{}/{}{}'.format(
        PROJECTS_RESOURCE_PATH,
        project_id,
        LOCATIONS_RESOURCE_PATH,
        location,
        SCHEMA_REGISTRIES_RESOURCE_PATH,
        schema_registry_id,
    )
    if args.context:
      name = f'{name}{CONTEXTS_RESOURCE_PATH}{args.context}'

    subject_resource_path = f'{name}/{SUBJECTS_RESOURCE_PATH}{subject}'

    print('Describing subject: {}'.format(subject_resource_path))

    subject_mode_request = (
        message.ManagedkafkaProjectsLocationsSchemaRegistriesModeGetRequest(
            name=f'{name}/mode/{subject}'
        )
    )
    subject_config_request = (
        message.ManagedkafkaProjectsLocationsSchemaRegistriesConfigGetRequest(
            name=f'{name}/config/{subject}'
        )
    )

    subject_mode = client.projects_locations_schemaRegistries_mode.Get(
        request=subject_mode_request
    )
    subject_config = client.projects_locations_schemaRegistries_config.Get(
        request=subject_config_request,
    )

    mode = util.ParseMode(subject_mode.mode)

    compatibility = util.ParseCompatibility(subject_config.compatibility)

    verbose_subject = {
        'name': subject_resource_path,
        'mode': mode,
        'compatibility': compatibility,
    }

    print(verbose_subject)

    return verbose_subject
