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
"""This module contains common utility function for GAE to CR migration."""
from collections.abc import Mapping, Sequence
import logging
from typing import Any, cast
from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app.gae_to_cr_migration_util.config import feature_helper
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files


class InvalidAppYamlPathError(exceptions.Error):
  """An error that is raised when invalid app.yaml path is provided."""

# Entrypoint for these runtimes must be specified in a Procfile
# instead of via the `--command` flag at the gcloud run deploy
# command.
ENTRYPOINT_FEATURE_KEYS: Sequence[str] = ['entrypoint', 'entrypoint.shell']
PYTHON_RUNTIMES_WITH_PROCFILE_ENTRYPOINT: Sequence[str] = [
    'python',
    'python37',
    'python38',
    'python39',
    'python310',
]
RUBY_RUNTIMES_WITH_PROCFILE_ENTRYPOINT: Sequence[str] = [
    'ruby',
    'ruby25',
    'ruby26',
    'ruby27',
    'ruby30',
]
RUNTIMES_WITH_PROCFILE_ENTRYPOINT: Sequence[str] = (
    PYTHON_RUNTIMES_WITH_PROCFILE_ENTRYPOINT
    + RUBY_RUNTIMES_WITH_PROCFILE_ENTRYPOINT
)
_FLATTEN_EXCLUDE_KEYS: Sequence[str] = ['env_variables', 'envVariables']
_ALLOW_FLEX_ENV_VALUES = ('flex', 'flexible')


def is_flex_env(input_data: Mapping[str, Any]) -> bool:
  """Detect whether input app.yaml is for flex environment."""

  return input_data.get('env') in _ALLOW_FLEX_ENV_VALUES


def generate_output_flags(flags: Sequence[str], value: str) -> Sequence[str]:
  """Generate output flags by given list of flag names and value."""
  if flags[0] == '--service-account' and value.endswith('"'):
    value = value[1:-1]
  return [f'{flag}={value}' for flag in flags]


def get_feature_key_from_input(
    input_key_value_pairs: Mapping[str, Any], allow_keys: Sequence[str]
) -> str:
  """Get feature key from input based on list of allowed keys."""
  allow_keys_from_input = [
      key for key in input_key_value_pairs if key in allow_keys
  ]
  if not allow_keys_from_input:
    return None
  if len(allow_keys_from_input) > 1:
    logging.error(
        '[Error] Conflicting configurations found: %s.   '
        '      Please ensure only one is specified".',
        allow_keys_from_input,
    )
    return None
  return allow_keys_from_input[0]


def get_features_by_prefix(
    features: Mapping[str, feature_helper.Feature], prefix: str
) -> Mapping[str, feature_helper.Feature]:
  """Return a dict of features matched with the prefix."""
  return {
      key: value
      for key, value in features.items()
      if key.startswith(prefix) and value is not None
  }


def flatten_keys(
    input_data: Mapping[str, Any],
    parent_path: str,
) -> Mapping[str, Any]:
  """Flatten nested paths (root to leaf) of a dictionary to a single level.

  Args:
      input_data: The input dictionary to be flattened.
      parent_path: The parent path of the input dictionary.
  Returns:
      A dictionary with flattened paths.
  For example:
      Input: {
          "resources": {
              "cpu": 5,
              "memory_gb": 10
          }
      }
      output: {
          "resources.cpu": 5,
          "resources.memory_gb": 10
      }
  }
  """
  paths = {}
  for key in input_data:
    curr_path = f'{parent_path}.{key}' if parent_path else key
    if not isinstance(input_data[key], Mapping) or key in _FLATTEN_EXCLUDE_KEYS:
      paths[curr_path] = input_data[key]
    else:
      paths.update(flatten_keys(input_data[key], curr_path))
  return paths


def get_version_data(
    *,
    appyaml: str | None = None,
    service: str | None = None,
    version: str | None = None,
) -> tuple[Mapping[str, Any], feature_helper.InputType]:
  """Retrieves input data as Python objects.

  This function fetches input data either from an `app.yaml` file or
  by calling the App Engine Admin API, depending on whether `appyaml` or
  both `service` and `version` are provided.

  Args:
    appyaml: The path to the app.yaml file. If provided, data is read from here.
    service: The service name. Required along with `version` to fetch from the
      App Engine Admin API.
    version: The version name. Required along with `service` to fetch from the
      App Engine Admin API.

  Returns:
    A tuple containing:
    -   A mapping of the input data as Python objects, or None if the
        input data could not be retrieved.
    -   The feature_helper.InputType (either ADMIN_API or APP_YAML).
  """

  appyaml_param_specified = appyaml is not None
  deployed_version_specified = service is not None and version is not None
  if appyaml_param_specified and deployed_version_specified:
    logging.error(
        '[Error] Invalid input, only one of app.yaml or deployed               '
        '   version can be used as an input. Use --appyaml flag t            '
        '     specify the app.yaml, or use --service and --version             '
        '     to specify the deployed version.'
    )
    return (None, None)

  # If user runs `gcloud app migrate app-engine-to-cloudrun`
  # without providing any parameters,
  # it assumes the current directory has an `app.yaml` file by default.
  if not deployed_version_specified and not appyaml_param_specified:
    appyaml = 'app.yaml'
  input_type = (
      feature_helper.InputType.ADMIN_API
      if deployed_version_specified
      else feature_helper.InputType.APP_YAML
  )

  return (
      _get_input_data_by_input_type(
          input_type=input_type,
          appyaml=appyaml,
          service=service,
          version=version,
      ),
      input_type,
  )


def _get_input_data_by_input_type(
    *,
    input_type: feature_helper.InputType,
    appyaml: str,
    service: str,
    version: str,
) -> Mapping[str, Any]:
  """Gets the input data by input type."""

  # deployed version is input type
  if input_type == feature_helper.InputType.ADMIN_API:
    api_client = appengine_api_client.GetApiClientForTrack(base.ReleaseTrack.GA)
    gcloud_output = api_client.GetVersionResource(
        service=service, version=version
    )
    if gcloud_output is None:
      logging.error('gcloud_output is empty.')
      return None

    version_data = {
        'automaticScaling': gcloud_output.automaticScaling,
        'basicScaling': gcloud_output.basicScaling,
        'createTime': gcloud_output.createTime,
        'manualScaling': gcloud_output.manualScaling,
        'createdBy': gcloud_output.createdBy,
        'deployment': gcloud_output.deployment,
        'diskUsageBytes': gcloud_output.diskUsageBytes,
        'env': gcloud_output.env,
        'errorHandlers': gcloud_output.errorHandlers,
        'handlers': gcloud_output.handlers,
        'id': gcloud_output.id,
        'inboundServices': gcloud_output.inboundServices,
        'instanceClass': gcloud_output.instanceClass,
        'libraries': gcloud_output.libraries,
        'name': gcloud_output.name,
        'network': gcloud_output.network,
        'runtime': gcloud_output.runtime,
        'runtimeChannel': gcloud_output.runtimeChannel,
        'serviceAccount': gcloud_output.serviceAccount,
        'servingStatus': gcloud_output.servingStatus,
        'threadsafe': gcloud_output.threadsafe,
        'versionUrl': gcloud_output.versionUrl,
        'zones': gcloud_output.zones,
        'appEngineApis': gcloud_output.appEngineApis,
        'livenessCheck': gcloud_output.livenessCheck,
        'readinessCheck': gcloud_output.readinessCheck,
        'resources': gcloud_output.resources,
        'entrypoint': gcloud_output.entrypoint,
    }
    if gcloud_output.envVariables is not None:
      version_data.update(
          {'envVariables': cast(
              Mapping[str, str], gcloud_output.envVariables.additionalProperties
          )}
      )
    if getattr(gcloud_output, 'buildEnvVariables', None) is not None:
      version_data['build_env_variables'] = {
          prop.key: prop.value
          for prop in gcloud_output.buildEnvVariables.additionalProperties
      }
    if getattr(gcloud_output, 'runtimeConfig', None) is not None:
      version_data['runtime_config'] = {
          prop.key: prop.value
          for prop in gcloud_output.runtimeConfig.additionalProperties
      }
    return version_data

  # appyaml is input type
  try:
    with files.FileReader(appyaml) as file:
      appyaml_data = yaml.load(file.read())
      if appyaml_data is None:
        logging.error('%s is empty.', file.name)
      return appyaml_data
  except files.MissingFileError:
    raise InvalidAppYamlPathError(
        'app.yaml does not exist in the provided directory, please use'
        ' --appyaml flag to specify the correct app.yaml location.'
    )
  return None


_DEFAULT_STACK_VERSION = '22'
_STACK_18_RUNTIMES: Sequence[str] = (
    'python37',
    'nodejs10',
    'nodejs12',
    'nodejs14',
    'php7',
    'ruby2',
    'go111',
    'go112',
    'go113',
    'go114',
    'go115',
    'go116',
)
_STACK_24_RUNTIMES: Sequence[str] = (
    'python313',
    'nodejs24',
    'java23',
    'go123',
    'php84',
    'ruby33',
)
_BASE_IMAGE_URI_FORMAT = (
    '{region}-docker.pkg.dev/serverless-runtimes/google-{stack_version}-full/'
    'runtimes/{base_runtime}'
)


def determine_base_image(
    input_data: Mapping[str, Any], region: str | None = None
) -> str | None:
  """Determines the base image URI from the App Engine configuration.

  Args:
    input_data: The configuration data parsed from input.
    region: The Google Cloud region, defaults to 'us-central1'.

  Returns:
    str | None: The URI of the base image, or None if it cannot be determined.
  """
  if not region:
    # For --export-only runs, region might not be provided/prompted, so we
    # default to 'us-central1' to construct a valid registry URL for the base
    # image.
    region = 'us-central1'
  runtime = input_data.get('runtime')
  runtime_config = input_data.get('runtime_config')
  base_image = None
  if runtime and runtime != 'custom':
    base_runtime = runtime
    stack_version = _DEFAULT_STACK_VERSION
    if runtime_config:
      if 'operating_system' in runtime_config:
        os_val = str(runtime_config['operating_system']).lower()
        if 'ubuntu' in os_val:
          stack_version = os_val.replace('ubuntu', '')
      for key, val in runtime_config.items():
        if key in (
            f'{runtime}_version',
            f'{runtime}Version',
            'runtime_version',
            'runtimeVersion',
        ):
          base_runtime = f'{runtime}{str(val).replace(".", "")}'
          break
        elif key == 'jdk':
          base_runtime = str(val).replace('openjdk', 'java')
          break
    if not base_runtime[-1].isdigit():
      return None
    if stack_version == _DEFAULT_STACK_VERSION and runtime:
      if any(runtime.startswith(prefix) for prefix in _STACK_18_RUNTIMES):
        stack_version = '18'
      elif any(runtime.startswith(prefix) for prefix in _STACK_24_RUNTIMES):
        stack_version = '24'
    base_image = _BASE_IMAGE_URI_FORMAT.format(
        region=region, stack_version=stack_version, base_runtime=base_runtime
    )
  return base_image
