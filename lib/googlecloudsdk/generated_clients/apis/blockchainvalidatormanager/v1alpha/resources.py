# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Resource definitions for Cloud Platform Apis generated from apitools."""

import enum


BASE_URL = 'https://blockchainvalidatormanager.googleapis.com/v1alpha/'
DOCS_URL = 'https://cloud.google.com/blockchain-node-engine/docs/create-node-ethereum#validator_configuration'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  PROJECTS = (
      'projects',
      'projects/{projectsId}',
      {},
      ['projectsId'],
      True
  )
  PROJECTS_LOCATIONS = (
      'projects.locations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_BLOCKCHAINNODES = (
      'projects.locations.blockchainNodes',
      'projects/{projectsId}/locations/{locationsId}/blockchainNodes/'
      '{blockchainNodeId}',
      {},
      ['projectsId', 'locationsId', 'blockchainNodeId'],
      True
  )
  PROJECTS_LOCATIONS_BLOCKCHAINVALIDATORCONFIGS = (
      'projects.locations.blockchainValidatorConfigs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'blockchainValidatorConfigs/{blockchainValidatorConfigsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_BLOCKCHAINVALIDATORTEMPLATES = (
      'projects.locations.blockchainValidatorTemplates',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'blockchainValidatorTemplates/{blockchainValidatorTemplatesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_OPERATIONS = (
      'projects.locations.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/operations/'
              '{operationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_SECRETS = (
      'projects.locations.secrets',
      'projects/{projectsId}/locations/{locationsId}/secrets/{secretsId}',
      {},
      ['projectsId', 'locationsId', 'secretsId'],
      True
  )
  PROJECTS_SECRETS = (
      'projects.secrets',
      'projects/{projectsId}/secrets/{secretsId}',
      {},
      ['projectsId', 'secretsId'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
