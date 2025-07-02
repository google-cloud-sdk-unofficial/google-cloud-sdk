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
"""Implementation of gcloud managed kafka schema registries describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.managed_kafka import arguments
from googlecloudsdk.command_lib.managed_kafka import util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

PROJECTS_RESOURCE_PATH = 'projects/'
LOCATIONS_RESOURCE_PATH = 'locations/'
SCHEMA_REGISTRIES_RESOURCE_PATH = 'schemaRegistries/'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class Describe(base.UpdateCommand):
  """Describe a schema registry with all of its fields.

  ## EXAMPLES

   Describe the schema registry with all of its fields:

    $ {command} --project=PROJECT_ID --location=LOCATION_ID
    --schema_registry=SCHEMA_REGISTRY_ID
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""

    arguments.AddSchemaRegistryArgToParser(parser)

  def Run(self, args):
    """Called when the user runs gcloud managed-kafka schema-registries describe ...

    Args:
      args: all the arguments that were provided to this command invocation.

    Returns:
      The schema registry.
    """
    message = apis.GetMessagesModule('managedkafka', 'v1')
    client = apis.GetClientInstance('managedkafka', 'v1')

    project_id = util.ParseProject(args.project)
    location = args.location

    schema_registry_resource = resources.REGISTRY.Parse(
        args.schema_registry,
        collection='managedkafka.projects.locations.schemaRegistries',
        params={
            'projectsId': project_id,
            'locationsId': location,
            'schemaRegistriesId': args.schema_registry,
        },
    )

    schema_registry_path = schema_registry_resource.RelativeName()

    log.status.Print(
        'Describing schema registry: {}'.format(schema_registry_path) + '\n'
    )

    schema_registry_request = (
        message.ManagedkafkaProjectsLocationsSchemaRegistriesGetRequest(
            name=schema_registry_path
        )
    )
    schema_registry_mode_request = (
        message.ManagedkafkaProjectsLocationsSchemaRegistriesModeGetRequest(
            name=f'{schema_registry_path}/mode'
        )
    )
    schema_registry_config_request = (
        message.ManagedkafkaProjectsLocationsSchemaRegistriesConfigGetRequest(
            name=f'{schema_registry_path}/config'
        )
    )

    schema_registry = client.projects_locations_schemaRegistries.Get(
        request=schema_registry_request
    )
    schema_registry_mode = client.projects_locations_schemaRegistries_mode.Get(
        request=schema_registry_mode_request
    )
    schema_registry_config = (
        client.projects_locations_schemaRegistries_config.Get(
            request=schema_registry_config_request,
        )
    )

    mode = util.ParseMode(schema_registry_mode.mode)

    compatibility = util.ParseCompatibility(
        schema_registry_config.compatibility
    )

    verbose_schema_registry = {
        'name': schema_registry.name,
        'contexts': schema_registry.contexts,
        'mode': mode,
        'compatibility': compatibility,
    }

    log.status.Print('name: {}'.format(verbose_schema_registry['name']))
    log.status.Print('mode: {}'.format(verbose_schema_registry['mode']))
    log.status.Print('config:')
    log.status.Print(
        '  - compatibility: {}'.format(verbose_schema_registry['compatibility'])
    )
    log.status.Print('contexts:')
    for context in verbose_schema_registry['contexts']:
      log.status.Print('  - {}'.format(context))

    return verbose_schema_registry
