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


BASE_URL = 'https://datalineage.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/data-catalog'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  FOLDERS = (
      'folders',
      'folders/{foldersId}',
      {},
      ['foldersId'],
      True
  )
  FOLDERS_LOCATIONS = (
      'folders.locations',
      'folders/{foldersId}/locations/{locationsId}',
      {},
      ['foldersId', 'locationsId'],
      True
  )
  FOLDERS_LOCATIONS_CONFIG = (
      'folders.locations.config',
      '{+name}',
      {
          '':
              'folders/{foldersId}/locations/{locationsId}/config',
      },
      ['name'],
      True
  )
  ORGANIZATIONS = (
      'organizations',
      'organizations/{organizationsId}',
      {},
      ['organizationsId'],
      True
  )
  ORGANIZATIONS_LOCATIONS = (
      'organizations.locations',
      'organizations/{organizationsId}/locations/{locationsId}',
      {},
      ['organizationsId', 'locationsId'],
      True
  )
  ORGANIZATIONS_LOCATIONS_CONFIG = (
      'organizations.locations.config',
      '{+name}',
      {
          '':
              'organizations/{organizationsId}/locations/{locationsId}/config',
      },
      ['name'],
      True
  )
  PROJECTS = (
      'projects',
      'projects/{projectsId}',
      {},
      ['projectsId'],
      True
  )
  PROJECTS_LOCATIONS = (
      'projects.locations',
      'projects/{projectsId}/locations/{locationsId}',
      {},
      ['projectsId', 'locationsId'],
      True
  )
  PROJECTS_LOCATIONS_CONFIG = (
      'projects.locations.config',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/config',
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
  PROJECTS_LOCATIONS_PROCESSES = (
      'projects.locations.processes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/processes/'
              '{processesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_PROCESSES_RUNS = (
      'projects.locations.processes.runs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/processes/'
              '{processesId}/runs/{runsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_PROCESSES_RUNS_LINEAGEEVENTS = (
      'projects.locations.processes.runs.lineageEvents',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/processes/'
              '{processesId}/runs/{runsId}/lineageEvents/{lineageEventsId}',
      },
      ['name'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
