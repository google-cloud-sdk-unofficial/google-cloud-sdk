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
"""Implementation of gcloud managed kafka schema registries subject update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.managed_kafka import arguments
from googlecloudsdk.generated_clients.apis.managedkafka.v1 import managedkafka_v1_messages


_MESSAGE = apis.GetMessagesModule('managedkafka', 'v1')
_CLIENT = apis.GetClientInstance('managedkafka', 'v1', no_http=True)

PROJECTS_RESOURCE_PATH = 'projects/'
LOCATIONS_RESOURCE_PATH = 'locations/'
SCHEMA_REGISTRIES_RESOURCE_PATH = 'schemaRegistries/'
SUBJECTS_RESOURCE_PATH = 'subjects/'
CONTEXTS_RESOURCE_PATH = '/contexts/'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.DefaultUniverseOnly
class Update(base.UpdateCommand):
  """Update the mode and compatibility of a subject.

  ## EXAMPLES

  Modify the mode of the subject to READONLY:

    $ {command} --mode=READONLY

  Modify the compatibility of the subject to BACKWARDS:

    $ {command} --compatibility=BACKWARDS
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    arguments.AddSubjectArgToParser(parser)

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

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        '--mode',
        type=str,
        help='The mode and compatibility of the schema registry.',
    )
    group.add_argument(
        '--compatibility',
        type=str,
        help='The mode and compatibility of the schema registry.',
    )

  def Run(self, args):
    """Called when the user runs gcloud managed-kafka schema-registries update ...

    Args:
      args: all the arguments that were provided to this command invocation.

    Returns:
      The updated schema registry.
    """
    project_id = args.project
    location = args.location
    schema_registry_id = args.schema_registry
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

    if args.mode:
      name = f'{name}/mode/{args.CONCEPTS.subject.Parse().subjectsId}'
      updatemoderequest = _MESSAGE.UpdateSchemaModeRequest()
      updatemoderequest.mode = (
          managedkafka_v1_messages.UpdateSchemaModeRequest.ModeValueValuesEnum(
              args.mode
          )
      )
      # Check if context is provided.
      if args.context:
        request = _MESSAGE.ManagedkafkaProjectsLocationsSchemaRegistriesContextsModeUpdateRequest(
            name=name, updateSchemaModeRequest=updatemoderequest
        )
        response = (
            _CLIENT.projects_locations_schemaRegistries_contexts_mode.Update(
                request=request
            )
        )
      else:
        request = _MESSAGE.ManagedkafkaProjectsLocationsSchemaRegistriesModeUpdateRequest(
            name=name, updateSchemaModeRequest=updatemoderequest
        )
        response = _CLIENT.projects_locations_schemaRegistries_mode.Update(
            request=request
        )

      print('Updated subject mode to %s' % response.mode)

    if args.compatibility:
      name = f'{name}/config/{args.CONCEPTS.subject.Parse().subjectsId}'
      updateconfigrequest = _MESSAGE.UpdateSchemaConfigRequest()
      updateconfigrequest.compatibility = managedkafka_v1_messages.UpdateSchemaConfigRequest.CompatibilityValueValuesEnum(
          args.compatibility
      )
      # Check if context is provided.
      if args.context:
        request = _MESSAGE.ManagedkafkaProjectsLocationsSchemaRegistriesContextsConfigUpdateRequest(
            name=name, updateSchemaConfigRequest=updateconfigrequest
        )
        response = (
            _CLIENT.projects_locations_schemaRegistries_contexts_config.Update(
                request=request
            )
        )
      else:
        request = _MESSAGE.ManagedkafkaProjectsLocationsSchemaRegistriesConfigUpdateRequest(
            name=name, updateSchemaConfigRequest=updateconfigrequest
        )
        response = _CLIENT.projects_locations_schemaRegistries_config.Update(
            request=request
        )

      print('Updated subject compatibility to %s' % response.compatibility)
      # TODO: b/418768300 - Add normalize and alias to the output once they
      # are supported.
      print(
          'Current subject config is \n compatibility = %s'
          % (response.compatibility)
      )
