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


BASE_URL = 'https://serviceusage.googleapis.com/v2beta/'
DOCS_URL = 'https://cloud.google.com/service-usage/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  CONSUMERPOLICIES = (
      'consumerPolicies',
      '{+name}',
      {
          '':
              '{v2betaId}/{v2betaId1}/consumerPolicies/{consumerPoliciesId}',
      },
      ['name'],
      True
  )
  OPERATIONS = (
      'operations',
      '{+name}',
      {
          '':
              'operations/{operationsId}',
      },
      ['name'],
      True
  )
  SERVICES = (
      'services',
      '{+name}',
      {
          '':
              '{v2betaId}/{v2betaId1}/services/{servicesId}',
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
