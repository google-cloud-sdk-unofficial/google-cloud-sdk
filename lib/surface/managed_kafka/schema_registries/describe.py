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


_MESSAGE = apis.GetMessagesModule('managedkafka', 'v1')
_CLIENT = apis.GetClientInstance('managedkafka', 'v1', no_http=True)

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

    project_id = args.project
    location = args.location

    name = '{}{}/{}{}/{}{}'.format(
        PROJECTS_RESOURCE_PATH,
        project_id,
        LOCATIONS_RESOURCE_PATH,
        location,
        SCHEMA_REGISTRIES_RESOURCE_PATH,
        args.CONCEPTS.schema_registry.Parse().schemaRegistriesId,
    )

    print('Describing schema registry: {}'.format(name))
    schema_registry = _MESSAGE.SchemaRegistry()
    schema_registry.name = name
    schema_registry_request = (
        _MESSAGE.ManagedkafkaProjectsLocationsSchemaRegistriesGetRequest(
            name=name
        )
    )
    schema_registry_mode_request = (
        _MESSAGE.ManagedkafkaProjectsLocationsSchemaRegistriesModeGetRequest(
            name=name + '/mode'
        )
    )
    schema_registry_config_request = (
        _MESSAGE.ManagedkafkaProjectsLocationsSchemaRegistriesConfigGetRequest(
            name=name + '/config'
        )
    )

    schema_registry = _CLIENT.projects_locations_schemaRegistries.Get(
        request=schema_registry_request
    )
    schema_registry_mode = _CLIENT.projects_locations_schemaRegistries_mode.Get(
        request=schema_registry_mode_request
    )
    schema_registry_config = (
        _CLIENT.projects_locations_schemaRegistries_config.Get(
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

    print(verbose_schema_registry)

    return verbose_schema_registry
