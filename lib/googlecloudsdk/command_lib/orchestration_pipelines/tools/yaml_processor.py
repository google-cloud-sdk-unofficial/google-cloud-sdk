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
"""Common utilities for Orchestration Pipelines commands."""

import re
from typing import Any, Dict, Optional

from googlecloudsdk.command_lib.orchestration_pipelines import deployment_model
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

ARTIFACT_STORAGE_KEY = "artifact_storage"
ENVIRONMENTS_KEY = "environments"
VARIABLES_KEY = "variables"
RESOURCES_KEY = "resources"


class BadFileError(exceptions.Error):
  """Raised when the file is not valid."""

  pass


def _resolve_string_templates(yaml_content, variables):
  for key, value in variables.items():
    placeholder_pattern = r"{{\s*" + re.escape(key) + r"\s*}}"
    # Use a lambda to evaluate str(value) only if a match is found.
    # This allows passing objects that raise errors on __str__ conversion
    # to control when that error occurs (only if used).
    yaml_content = re.sub(
        placeholder_pattern, lambda m, v=value: str(v), yaml_content
    )
  return yaml_content


def _check_for_missing_variables(content):
  """Checks if there are any unsubstituted variables in the content."""
  pattern = r"{{\s*([A-Za-z0-9_]+)\s*}}"
  match = re.search(pattern, content)
  if match:
    var_name = match.group(1)
    raise BadFileError(
        f"Variable '{var_name}' not found in deployment file 'deployment.yaml' "
        "variables section, nor in environment variables "
        f"(as _DEPLOY_VAR_{var_name})."
    )


def _get_updated_path_info(raw_path, bundle_dag_prefix):
  """Returns GCS path and clean path if raw_path needs to be updated."""
  if raw_path and not raw_path.startswith("/home/airflow/gcs/"):
    clean_path = raw_path[2:] if raw_path.startswith("./") else raw_path
    gcs_path = f"/home/airflow/gcs/{bundle_dag_prefix}/{clean_path}"
    return gcs_path, clean_path
  return None, None


def resolve_dynamic_variables(
    yaml_content: str,
    deployment_path: str,
    env: str,
    external_variables: Optional[Dict[str, Any]] = None,
    bundle_dag_prefix: Optional[str] = None,
) -> Any:
  """Resolves dynamic variables in the YAML content.

  This function substitutes environment variables and other dynamic values
  into the provided YAML content.

  Args:
    yaml_content: The content of the YAML file to be resolved.
    deployment_path: The path to the deployment configuration YAML file.
    env: The environment to use (e.g., "dev", "staging", "prod").
    external_variables: Optional dict of external variables to substitute.
    bundle_dag_prefix: The prefix for the bundle DAG.

  Returns:
    The resolved_yaml_content YAML file content as a string.
  """

  parsed_deployment = parse_deployment(deployment_path, env, external_variables)

  combined_variables = {
      "project": parsed_deployment["project"],
      "region": parsed_deployment["region"],
      **parsed_deployment.get(VARIABLES_KEY, {}),
  }

  resolved_yaml_content = _resolve_string_templates(
      yaml_content, combined_variables
  )
  try:
    resolved_yaml_content = yaml.load(resolved_yaml_content)
  except yaml.YAMLParseError as e:
    raise BadFileError(
        f"Failed to parse pipeline YAML after variable substitution:: {e}"
    )

  if (
      isinstance(resolved_yaml_content, dict)
      and "actions" in resolved_yaml_content
  ):
    resolved_yaml_content = _resolve_pipeline_yaml(
        resolved_yaml_content,
        combined_variables,
        parsed_deployment,
        bundle_dag_prefix,
    )
  return resolved_yaml_content


def _resolve_pipeline_yaml(
    yaml_content, combined_variables, deployment, bundle_dag_prefix
):
  """Resolves pipeline specific configurations within the YAML content."""

  for action in yaml_content.get("actions", []):
    if ARTIFACT_STORAGE_KEY in deployment:
      action["depsBucket"] = deployment[ARTIFACT_STORAGE_KEY]["bucket"]

    config = action.get("config", {})
    resource_profile = config.get("resourceProfile")
    profile_definition = {}
    if isinstance(resource_profile, dict) and "path" in resource_profile:
      profile_path = resource_profile["path"]
      try:
        raw_profile_content = files.ReadFileContents(profile_path)
        resolved_profile_str = _resolve_string_templates(
            raw_profile_content, combined_variables
        )
        profile_definition = yaml.load(resolved_profile_str)
      except (IOError, OSError, yaml.Error) as e:
        raise BadFileError(
            f"Error reading or parsing resource profile '{profile_path}': {e}"
        ) from e
    engine_raw = action.get("engine")
    if isinstance(engine_raw, dict):
      engine_type = engine_raw.get("engineType")
    else:
      engine_type = engine_raw
    if engine_type == "dataproc-serverless":
      config["resourceProfile"] = profile_definition.get("definition", {})
    elif engine_type == "dataproc-gce":
      del config["resourceProfile"]
      config.update(profile_definition.get("definition", {}))

    if engine_type == "dbt":
      source = config.setdefault("source", {})
      raw_path = source.get("path", "")
      gcs_path, clean_path = _get_updated_path_info(raw_path, bundle_dag_prefix)
      if gcs_path:
        source["path"] = gcs_path
        action["_local_dag_upload_path"] = clean_path
    if engine_type == "dataform":
      raw_path = config.get("dataformProjectPath", "")
      gcs_path, clean_path = _get_updated_path_info(raw_path, bundle_dag_prefix)
      if gcs_path:
        config["dataformProjectPath"] = gcs_path
        action["_local_dag_upload_path"] = clean_path

  return yaml_content


def load_environment(
    deployment_path: str,
    env: str,
    external_variables: Optional[Dict[str, Any]] = None,
) -> deployment_model.EnvironmentModel:
  """Loads the deployment environment configuration."""
  try:
    # 1. Read raw content
    yaml_content = files.ReadFileContents(deployment_path)

    # 2. Parse strictly to get variables
    # We mask jinja2-style templates {{ ... }} to make it valid YAML for the
    # first pass. We replace {{ with __OPEN_TAG__ and }} with __CLOSE_TAG__
    # so that "name: {{ VAR }}" becomes
    # "name: __OPEN_TAG__ VAR __CLOSE_TAG__" which is a valid string.
    masked_content = yaml_content.replace("{{", "__OPEN_TAG__").replace(
        "}}", "__CLOSE_TAG__")

    pre_deployment_yaml = yaml.load(masked_content)

    # Extract internal variables
    internal_variables = {}
    if (
        pre_deployment_yaml
        and ENVIRONMENTS_KEY in pre_deployment_yaml
        and env in pre_deployment_yaml[ENVIRONMENTS_KEY]
        and VARIABLES_KEY in pre_deployment_yaml[ENVIRONMENTS_KEY][env]
    ):
      # We need to revert the masking in the values of variables if they had any
      raw_vars = pre_deployment_yaml[ENVIRONMENTS_KEY][env][VARIABLES_KEY] or {}
      for k, v in raw_vars.items():
        if isinstance(v, str):
          internal_variables[k] = v.replace("__OPEN_TAG__", "{{").replace(
              "__CLOSE_TAG__", "}}")
        else:
          internal_variables[k] = v

    if external_variables:
      internal_variables.update(external_variables)

    # 3. Substitute on raw content
    resolved_content = _resolve_string_templates(
        yaml_content, internal_variables)

    _check_for_missing_variables(resolved_content)

    # 4. Final Parse
    deployment_yaml = yaml.load(resolved_content)

  except yaml.YAMLParseError as e:
    raise BadFileError(f"Error parsing deployment.yaml: {e}")

  try:
    deployment = deployment_model.DeploymentModel.build(deployment_yaml)
  except (KeyError, TypeError, ValueError, AttributeError) as e:
    raise BadFileError(f"Error parsing deployment configuration: {e}") from e

  environments = getattr(deployment, ENVIRONMENTS_KEY)
  if env not in environments:
    raise BadFileError(f"Environment '{env}' not found in deployment file.")

  return environments[env]


def validate_environment(
    environment: deployment_model.EnvironmentModel, env: str
) -> deployment_model.EnvironmentModel:
  """Validates the deployment environment configuration.

  Args:
    environment: The deployment_model.EnvironmentModel object.
    env: The environment name to validate.

  Returns:
    The environment model (for chaining if needed).

  Raises:
    BadFileError: If the environment or configuration is invalid.
  """
  if not isinstance(environment, deployment_model.EnvironmentModel):
    raise BadFileError(
        f"Environment '{env}' is not a valid object in deployment file."
    )
  if environment.artifact_storage:
    if not isinstance(
        environment.artifact_storage,
        deployment_model.ArtifactStorageModel,
    ):
      raise BadFileError(
          f"Environment '{env}' has invalid artifact_storage in deployment"
          " file."
      )
  if not environment.variables:
    log.info(f"Environment '{env}' has no variables in deployment file.")
  else:
    if not isinstance(environment.variables, dict):
      raise BadFileError(
          f"Error: '{VARIABLES_KEY}' for environment '{env}' in deployment.yaml"
          " is not a dictionary"
      )
  return environment


def parse_deployment(
    deployment_path: str,
    env: str,
    external_variables: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
  """Extracts storage and environment specific configuration."""
  environment = load_environment(deployment_path, env, external_variables)
  environment = validate_environment(environment, env)

  result = {
      "project": environment.project,
      "region": environment.region,
      "resources": environment.resources,
  }

  if environment.artifact_storage:
    result[ARTIFACT_STORAGE_KEY] = {
        "bucket": environment.artifact_storage.bucket,
        "path_prefix": environment.artifact_storage.path_prefix,
    }

  if environment.composer_environment:
    result["composer_env"] = environment.composer_environment
  if environment.pipelines:
    result["pipelines"] = environment.pipelines
  if environment.variables:
    result["variables"] = environment.variables

  return result
