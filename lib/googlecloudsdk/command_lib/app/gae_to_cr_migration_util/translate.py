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

"""Translate module for GAE to Cloud Run conversion.

This module contains the implementation for conversion of App Engine app.yaml or
deployed version to Cloud Run.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.common import util
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.config import feature_helper
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.translation_rules import concurrent_requests
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.translation_rules import cpu_memory
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.translation_rules import entrypoint
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.translation_rules import required_flags
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.translation_rules import scaling
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.translation_rules import supported_features
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.translation_rules import timeout
from googlecloudsdk.core import properties


ExportImageResult = appengine_api_client.ExportImageResult


def translate_from_source(
    appyaml: str, service: str, version: str, entrypoint_command: str
) -> Sequence[str]:
  """Translates GAE app config to a Cloud Run deploy command.

  This function converts an App Engine app.yaml or a deployed version's
  configuration into a `gcloud run deploy` command.

  Args:
    appyaml: The path to the app.yaml file.
    service: The App Engine service to migrate.
    version: The App Engine version to migrate.
    entrypoint_command: The entrypoint command for the Cloud Run service.

  Returns:
    A sequence of strings representing the gcloud run deploy command.
  """
  input_type, input_data = util.validate_input(appyaml, service, version)
  if not input_type or not input_data:
    return []
  target_service = (
      service or _get_service_name(input_data)
  )
  input_flatten_as_appyaml = (
      util.flatten_keys(input_data, parent_path='')
      if input_type == feature_helper.InputType.APP_YAML
      else _convert_admin_api_input_to_app_yaml(input_data)
  )
  source_path = _get_source_path(input_type, appyaml)

  flags: Sequence[str] = _get_cloud_run_flags(
      input_data=input_data,
      input_flatten_as_appyaml=input_flatten_as_appyaml,
      input_type=input_type,
      entrypoint_command=entrypoint_command,
      source_path=source_path,
      runtime_base_image=None,
  )
  return _generate_output(target_service, flags, source_path, None)


def translate_from_image(
    service: str,
    version: str,
    entrypoint_command: str,
    export_image_response: ExportImageResult,
) -> Sequence[str]:
  """Translates a deployed GAE version to Cloud Run command via image export.

  Args:
    service: The App Engine service to migrate.
    version: The App Engine version to migrate.
    entrypoint_command: The entrypoint command for the Cloud Run service.
    export_image_response: An ExportImageResult object containing the exported
      image URI, runtime ID, and runtime base image.

  Returns:
    A sequence of strings representing the gcloud run deploy command.
  """
  input_type, input_data = util.validate_input(None, service, version)
  if not input_type or not input_data:
    return []
  target_service = (
      service or _get_service_name(input_data)
  )
  input_flatten_as_appyaml = _convert_admin_api_input_to_app_yaml(input_data)
  if export_image_response is not None:
    image = export_image_response.image_uri
    runtime_base_image = export_image_response.runtime_base_image
  else:
    image, runtime_base_image = None, None
  flags: Sequence[str] = _get_cloud_run_flags(
      input_data=input_data,
      input_flatten_as_appyaml=input_flatten_as_appyaml,
      input_type=input_type,
      entrypoint_command=entrypoint_command,
      source_path=None,
      runtime_base_image=runtime_base_image,
  )
  return _generate_output(
      target_service,
      flags,
      None,
      image,
  )


def _get_source_path(
    input_type: feature_helper.InputType, appyaml: str
) -> str:
  """Gets the source path for the Cloud Run deploy command."""
  if input_type == feature_helper.InputType.APP_YAML:
    source_path = appyaml.rsplit('app.yaml', 1)[0] if appyaml else ''
    if not source_path:
      source_path = '.'
    return source_path
  else:
    return input(
        'Is the source code located in the current directory? If not, please'
        ' provide its path relative to the current directory: '
    ) + '/'


def _convert_admin_api_input_to_app_yaml(
    admin_api_input_data: Mapping[str, Any],
) -> Mapping[str, Any]:
  """Converts the input from admin api to app yaml."""
  input_key_value_pairs = util.flatten_keys(
      admin_api_input_data, parent_path=''
  )
  feature_config = feature_helper.get_feature_config()
  translatable_features: Mapping[str, feature_helper.Feature] = {}
  translatable_features.update(
      feature_helper.get_feature_list_by_input_type(
          feature_helper.InputType.ADMIN_API, feature_config.range_limited
      )
  )
  translatable_features.update(
      feature_helper.get_feature_list_by_input_type(
          feature_helper.InputType.ADMIN_API, feature_config.value_limited
      )
  )
  translatable_features.update(
      feature_helper.get_feature_list_by_input_type(
          feature_helper.InputType.ADMIN_API, feature_config.supported
      )
  )

  merged_keys = [
      key for key in input_key_value_pairs if key in translatable_features
  ]
  merged_features: list[feature_helper.Feature] = []
  for key in merged_keys:
    merged_features.append(translatable_features[key])
  app_yaml_input = {}
  for feature in merged_features:
    app_yaml_input[feature.path[feature_helper.InputType.APP_YAML.value]] = (
        input_key_value_pairs[
            feature.path[feature_helper.InputType.ADMIN_API.value]
        ]
    )
  if 'instanceClass' in admin_api_input_data:
    app_yaml_input['instance_class'] = input_key_value_pairs['instanceClass']
  return app_yaml_input


def _get_cloud_run_flags(
    input_data: Mapping[str, Any],
    input_flatten_as_appyaml: Mapping[str, Any],
    input_type: feature_helper.InputType,
    entrypoint_command: str, *,
    source_path: str | None,
    runtime_base_image: str | None,
) -> Sequence[str]:
  """Gets the cloud run flags for the given input data.

  Args:
    input_data: The original input data, either from app.yaml or the Admin API.
    input_flatten_as_appyaml: A flattened mapping of the input data, with keys
      translated to their app.yaml equivalents.
    input_type: The type of the input source (APP_YAML or ADMIN_API).
    entrypoint_command: The command to use as the container entrypoint.
    source_path: The path to the application's source code, if deploying from
      source. None if deploying from an image.
    runtime_base_image: The base image URL for the runtime, if provided during
      image export. None otherwise.

  Returns:
    A sequence of strings representing the Cloud Run flags.
  """

  feature_config = feature_helper.get_feature_config()
  range_limited_features_app_yaml = (
      feature_helper.get_feature_list_by_input_type(
          feature_helper.InputType.APP_YAML, feature_config.range_limited
      )
  )
  supported_features_app_yaml = feature_helper.get_feature_list_by_input_type(
      feature_helper.InputType.APP_YAML, feature_config.supported
  )
  project = properties.VALUES.core.project.Get()
  return (
      concurrent_requests.translate_concurrent_requests_features(
          input_flatten_as_appyaml, range_limited_features_app_yaml
      )
      + scaling.translate_scaling_features(
          input_flatten_as_appyaml, range_limited_features_app_yaml
      )
      + timeout.translate_timeout_features(input_flatten_as_appyaml)
      + supported_features.translate_supported_features(
          input_type,
          input_flatten_as_appyaml,
          supported_features_app_yaml,
          project,
      )
      + entrypoint.translate_entrypoint_features(entrypoint_command)
      + required_flags.translate_add_required_flags(
          input_data, source_path, runtime_base_image
      )
      + cpu_memory.translate_app_resources(input_data)
  )


def _get_service_name(input_data: Mapping[str, Any]) -> str:
  """Gets the service name from the input data."""
  if 'service' in input_data:
    custom_service_name = input_data['service'].strip()
    if custom_service_name:
      return custom_service_name
  return 'default'


def _generate_output(
    service_name: str,
    flags: Sequence[str],
    source_path: str | None,
    image: str | None,
) -> Sequence[str]:
  """Generates the output for the Cloud Run deploy command.

  Args:
    service_name: The name of the Cloud Run service.
    flags: A sequence of flags to include in the gcloud run deploy command.
    source_path: The path to the source code. If provided, the `--source` flag
      will be used.
    image: The URL of the container image. If provided, the `--image` flag will
      be used.

  Returns:
    A sequence of strings representing the gcloud run deploy command.
  """
  output = [
      'gcloud',
      'run',
      'deploy',
      f'{service_name}',
  ]
  if image is not None:
    output.extend([f'--image={image}'])
  elif source_path is not None:
    output.extend([f'--source={source_path}'])
  if flags is not None:
    output.extend(flags)
  return output
