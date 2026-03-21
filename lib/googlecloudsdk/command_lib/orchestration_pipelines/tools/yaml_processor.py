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

import os
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
  except yaml.Error as e:
    raise BadFileError(
        f"Failed to parse pipeline YAML after variable substitution:: {e}"
    ) from e

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
      try:
        selected_names = []
        if resource_profile.get("name"):
          selected_names = [resource_profile.get("name")]

        loaded = _load_resource_profile(
            resource_profile["path"],
            names=selected_names,
            context=combined_variables,
        )
        if loaded:
          profile_definition = loaded[0]
      except BadFileError as e:
        # pylint: disable=raise-missing-from
        raise BadFileError(f"Error processing resource profile: {e}")
    engine_raw = action.get("engine")
    if isinstance(engine_raw, dict):
      engine_type = engine_raw.get("engineType")
    else:
      engine_type = engine_raw
    if engine_type == "dataproc-serverless":
      config["resourceProfile"] = profile_definition.get("definition", {})
    elif engine_type == "dataproc-gce":
      config.pop("resourceProfile", None)
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


def _load_resource_profile(
    path: str,
    names: Optional[list[str]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> list[Dict[str, Any]]:
  """Loads resource definitions from a profile file.

  Args:
    path: Path to the profile file.
    names: Optional list of resource names to select from the profile.
    context: Optional dictionary of variables for substitution.

  Returns:
    A list of resource definitions (dicts).

  Raises:
    BadFileError: If the file cannot be read or parsed.
  """
  try:
    raw_content = files.ReadFileContents(path)
    if context:
      raw_content = _resolve_string_templates(raw_content, context)
    profile_data = yaml.load(raw_content)
  except (IOError, OSError, yaml.Error) as e:
    raise BadFileError(
        f"Error reading or parsing resource profile '{path}': {e}"
    ) from e

  if isinstance(profile_data, list):
    # Catalog mode
    if names:
      target_names = set(names)
      filtered_content = [
          r for r in profile_data if r.get("name") in target_names
      ]
      found_names = {r.get("name") for r in filtered_content}
      missing = target_names - found_names
      if missing:
        raise BadFileError(
            f"Resource profiles {missing} not found in catalog '{path}'"
        )
      return filtered_content
    else:
      return profile_data

  elif isinstance(profile_data, dict):
    return [profile_data]

  else:
    raise BadFileError(f"Invalid resource profile format in '{path}'")


def _expand_environment_resources(
    env_model: deployment_model.EnvironmentModel,
    deployment_path: str,
    context: Optional[Dict[str, Any]] = None,
) -> None:
  """Expands resource profiles into actual resources."""
  expanded_resources = []
  base_dir = os.path.dirname(str(deployment_path))

  for r in env_model.resources:
    if isinstance(r, deployment_model.ResourceProfileModel):
      path = r.path
      # Resolve path relative to deployment file
      if not os.path.isabs(path):
        path = os.path.join(base_dir, path)

      if r.name and r.names:
        raise ValueError(
            f"Resource profile at '{r.path}' cannot specify both 'name' and"
            " 'names'."
        )

      selected_names = r.names
      if r.name:
        selected_names = [r.name]

      loaded_defs = _load_resource_profile(
          path,
          names=selected_names,
          context=context,
      )

      # If we loaded a single resource and we have a specific name for it
      # in the profile, we should apply it (e.g. for single-file profiles
      # that don't specify name in the file).
      if r.name and len(loaded_defs) == 1:
        # We only override/set name if we have a single result
        # and we requested a specific name (or just one resource).
        # Note: if selected_names was used for catalog, loaded_defs might be
        # size 1 too. But if r.name is used, we know it was a single
        # selection intent.
        loaded_defs[0]["name"] = r.name

      for definition in loaded_defs:
        # Convert dict definition to ResourceModel
        expanded_resources.append(deployment_model.build_resource(definition))
    else:
      expanded_resources.append(r)

  env_model.resources = expanded_resources


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

  except yaml.Error as e:
    raise BadFileError(f"Error parsing deployment.yaml: {e}") from e

  try:
    deployment = deployment_model.DeploymentModel.build(deployment_yaml)
  except (KeyError, TypeError, ValueError, AttributeError) as e:
    raise BadFileError(f"Error parsing deployment configuration: {e}") from e

  environments = getattr(deployment, ENVIRONMENTS_KEY)
  if env not in environments:
    raise BadFileError(f"Environment '{env}' not found in deployment file.")

  # Expand resources after building the model
  _expand_environment_resources(
      environments[env], deployment_path, context=internal_variables
  )

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
