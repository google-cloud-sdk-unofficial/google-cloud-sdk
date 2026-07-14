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
"""CLI to message converter utilities for Firestore index create commands."""

from googlecloudsdk.api_lib.firestore import api_utils as fs_api_utils
from googlecloudsdk.command_lib.firestore import flags


def _BuildEnumMessage(enum_class, cli_val):
  """Maps a parsed CLI value safely to its corresponding proto Enum class."""
  if not cli_val:
    return None
  enum_name = cli_val.upper().replace('-', '_')
  return enum_class(enum_name)


def BuildIndexMessage(
    field_configs,
    query_scope,
    api_scope,
    multikey,
    density,
    unique,
    search_index_options,
):
  """Builds a GoogleFirestoreAdminV1Index message from parsed arguments."""
  messages = fs_api_utils.GetMessages()
  fields = [_BuildIndexFieldMessage(messages, fc) for fc in field_configs]

  index = messages.GoogleFirestoreAdminV1Index(
      fields=fields,
      queryScope=_BuildEnumMessage(
          messages.GoogleFirestoreAdminV1Index.QueryScopeValueValuesEnum,
          query_scope,
      ),
      apiScope=_BuildEnumMessage(
          messages.GoogleFirestoreAdminV1Index.ApiScopeValueValuesEnum,
          api_scope,
      ),
      density=_BuildEnumMessage(
          messages.GoogleFirestoreAdminV1Index.DensityValueValuesEnum,
          density,
      ),
      multikey=multikey,
      unique=unique,
      searchIndexOptions=_BuildSearchIndexOptionsMessage(
          messages, search_index_options
      ),
  )

  return index


def _BuildSearchIndexOptionsMessage(messages, search_index_options):
  """Maps parsed search index options to a GoogleFirestoreAdminV1SearchIndexOptions message."""
  if not search_index_options:
    return None

  return messages.GoogleFirestoreAdminV1SearchIndexOptions(
      textLanguage=search_index_options.get(
          flags.SEARCH_INDEX_OPTIONS_TEXT_LANGUAGE
      ),
      textLanguageOverrideFieldPath=search_index_options.get(
          flags.SEARCH_INDEX_OPTIONS_TEXT_LANGUAGE_OVERRIDE_FIELD_PATH
      ),
  )


def _BuildIndexFieldMessage(messages, fc):
  """Maps a parsed field config dict to a GoogleFirestoreAdminV1IndexField message."""
  return messages.GoogleFirestoreAdminV1IndexField(
      fieldPath=fc.get(flags.FIELD_CONFIG_FIELD_PATH),
      order=_BuildEnumMessage(
          messages.GoogleFirestoreAdminV1IndexField.OrderValueValuesEnum,
          fc.get(flags.FIELD_CONFIG_ORDER),
      ),
      arrayConfig=_BuildEnumMessage(
          messages.GoogleFirestoreAdminV1IndexField.ArrayConfigValueValuesEnum,
          fc.get(flags.FIELD_CONFIG_ARRAY_CONFIG),
      ),
      vectorConfig=_BuildVectorConfigMessage(
          messages, fc.get(flags.FIELD_CONFIG_VECTOR_CONFIG)
      ),
      searchConfig=_BuildSearchConfigMessage(
          messages, fc.get(flags.FIELD_CONFIG_SEARCH_CONFIG)
      ),
  )


def _BuildVectorConfigMessage(messages, vector_config):
  """Maps parsed vector config data to a GoogleFirestoreAdminV1VectorConfig message."""
  if not vector_config:
    return None

  flat_config = None
  if flags.FIELD_CONFIG_FLAT in vector_config:
    flat_config = messages.GoogleFirestoreAdminV1FlatIndex()

  return messages.GoogleFirestoreAdminV1VectorConfig(
      dimension=vector_config.get(flags.FIELD_CONFIG_DIMENSION),
      flat=flat_config,
  )


def _BuildSearchConfigMessage(messages, search_config):
  """Maps parsed search config data to a GoogleFirestoreAdminV1SearchConfig message."""
  if not search_config:
    return None

  text_spec = None
  if flags.FIELD_CONFIG_TEXT_SPEC in search_config:
    index_specs = [
        messages.GoogleFirestoreAdminV1SearchTextIndexSpec(
            indexType=_BuildEnumMessage(
                messages.GoogleFirestoreAdminV1SearchTextIndexSpec.IndexTypeValueValuesEnum,
                spec.get(flags.FIELD_CONFIG_INDEX_TYPE),
            ),
            matchType=_BuildEnumMessage(
                messages.GoogleFirestoreAdminV1SearchTextIndexSpec.MatchTypeValueValuesEnum,
                spec.get(flags.FIELD_CONFIG_MATCH_TYPE),
            ),
        )
        for spec in search_config[flags.FIELD_CONFIG_TEXT_SPEC].get(
            flags.FIELD_CONFIG_INDEX_SPECS, []
        )
    ]
    text_spec = messages.GoogleFirestoreAdminV1SearchTextSpec(
        indexSpecs=index_specs
    )

  geo_spec = None
  if flags.FIELD_CONFIG_GEO_SPEC in search_config:
    geo_spec = messages.GoogleFirestoreAdminV1SearchGeoSpec(
        geoJsonIndexingDisabled=search_config[flags.FIELD_CONFIG_GEO_SPEC].get(
            flags.FIELD_CONFIG_GEO_JSON_INDEXING_DISABLED
        )
    )

  return messages.GoogleFirestoreAdminV1SearchConfig(
      textSpec=text_spec, geoSpec=geo_spec
  )
