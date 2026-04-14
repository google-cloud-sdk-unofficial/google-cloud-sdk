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
import pathlib
import re
from typing import Any, Dict, Optional

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.orchestration_pipelines import deployment_model
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

DEPLOYMENT_FILE_NAME = "deployment.yaml"
ARTIFACT_STORAGE_KEY = "artifact_storage"
ENVIRONMENTS_KEY = "environments"
VARIABLES_KEY = "variables"
SECRETS_KEY = "secrets"
RESOURCES_KEY = "resources"


class BadFileError(exceptions.Error):
  """Raised when the file is not valid."""

  pass


def resolve_dynamic_variables(
    yaml_content: str,
    deployment_path: str,
    env: str,
    external_variables: Optional[Dict[str, Any]] = None,
) -> Any:
  """Resolves dynamic variables in the YAML content.

  This function substitutes environment variables and other dynamic values
  into the provided YAML content.

  Args:
    yaml_content: The content of the YAML file to be resolved.
    deployment_path: The path to the deployment configuration YAML file.
    env: The environment to use (e.g., "dev", "staging", "prod").
    external_variables: Optional dict of external variables to substitute.

  Returns:
    The resolved_yaml_content YAML file content as a string.
  """

  parsed_deployment = parse_deployment(deployment_path, env, external_variables)

  combined_variables = {
      "project": parsed_deployment["project"],
      "region": parsed_deployment["region"],
      **parsed_deployment.get(VARIABLES_KEY, {}),
  }

  resolved_yaml_content = resolve_string_templates(
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
        resolved_yaml_content, combined_variables, parsed_deployment
    )
  return resolved_yaml_content


def _resolve_resource_profile(
    resource_profile: Dict[str, Any], context: Dict[str, Any]
) -> Dict[str, Any]:
  """Resolves a resource profile.

  This function handles resource profiles defined either 'inline' or via a
  'path' reference to an external file.

  Args:
    resource_profile: The resource profile dictionary.
    context: A dictionary of variables for template substitution.

  Returns:
    The resolved resource profile.
  """
  if not isinstance(resource_profile, dict):
    return resource_profile

  if "inline" in resource_profile:
    return resource_profile  # Leave it completely intact
  elif "path" in resource_profile:
    try:
      selected_names = (
          [resource_profile["name"]] if resource_profile.get("name") else []
      )
      loaded = _load_resource_profile(
          resource_profile["path"],
          names=selected_names,
          context=context,
      )
      if loaded:
        return {"inline": loaded[0].get("definition", {})}
    except BadFileError as e:
      # pylint: disable=raise-missing-from
      raise BadFileError(f"Error processing resource profile: {e}")

  return resource_profile


def _resolve_pipeline_yaml(yaml_content, combined_variables, deployment):
  """Resolves pipeline specific configurations within the YAML content."""

  for action_item in yaml_content.get("actions", []):

    action_props = action_item
    action_type = None
    if isinstance(action_item, dict):
      if "pipeline" in action_item and isinstance(
          action_item["pipeline"], dict
      ):
        action_props = action_item["pipeline"]
        action_type = "pipeline"
      elif "pyspark" in action_item and isinstance(
          action_item["pyspark"], dict
      ):
        action_props = action_item["pyspark"]
        action_type = "pyspark"
      elif "notebook" in action_item and isinstance(
          action_item["notebook"], dict
      ):
        action_props = action_item["notebook"]
        action_type = "notebook"
      elif "sql" in action_item and isinstance(action_item["sql"], dict):
        action_props = action_item["sql"]
        action_type = "sql"
      elif "python" in action_item and isinstance(action_item["python"], dict):
        action_props = action_item["python"]
        action_type = "python"
      elif len(action_item) == 1:
        first_key = next(iter(action_item.keys()))
        if isinstance(action_item[first_key], dict):
          action_props = action_item[first_key]
          action_type = first_key

    if ARTIFACT_STORAGE_KEY in deployment and action_type in [
        "pyspark",
        "notebook",
    ]:
      action_props["staging_bucket"] = deployment[ARTIFACT_STORAGE_KEY][
          "bucket"
      ]

    engine = action_props.get("engine", {})
    framework = action_props.get("framework", {})

    if isinstance(engine, dict):
      engine_type = next(iter(engine.keys()), None)
    else:
      engine_type = engine

    # Handle Dataproc Serverless ---
    if engine_type == "dataprocServerless":
      dp_serverless = engine["dataprocServerless"]
      if "resourceProfile" in dp_serverless:
        dp_serverless["resourceProfile"] = _resolve_resource_profile(
            dp_serverless["resourceProfile"], combined_variables
        )

    # Handle Dataproc on GCE (Ephemeral) ---
    elif engine_type == "dataprocOnGce":
      ephemeral_cluster = engine[engine_type].get("ephemeralCluster", {})
      if "resourceProfile" in ephemeral_cluster:
        ephemeral_cluster["resourceProfile"] = _resolve_resource_profile(
            ephemeral_cluster["resourceProfile"], combined_variables
        )

    # Extract Local Upload Paths for Frameworks, SQL, and Python ---
    raw_upload_path = None

    if "dbt" in framework:
      raw_upload_path = (
          framework["dbt"]
          .setdefault("airflowWorker", {})
          .get("projectDirectoryPath", "")
      )
    elif "dataform" in framework:
      raw_upload_path = (
          framework["dataform"]
          .setdefault("airflowWorker", {})
          .get("projectDirectoryPath", "")
      )
    elif action_type == "sql":
      raw_upload_path = action_props.get("query", {}).get("path", "")
    elif action_type == "python":
      main_file = action_props.get("mainFilePath", "")
      if main_file and not main_file.startswith("gs://"):
        raw_upload_path = main_file

    if raw_upload_path:
      clean_path = (
          raw_upload_path[2:]
          if raw_upload_path.startswith("./")
          else raw_upload_path
      )
      action_item["_local_framework_upload_path"] = clean_path

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
      raw_content = resolve_string_templates(raw_content, context)
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


def _build_orchestration_pipelines_model(resolved_pipeline: Dict[str, Any]):
  """Validates a pipeline definition against a specific model version.

  This function extracts the 'model_version' from the provided definition,
  selects the corresponding Orchestration Pipelines model, and performs
  validation.

  Args:
    resolved_pipeline: The parsed YAML content of the pipeline.

  Raises:
    exceptions.Error: If the pipeline definition fails to build against the
      model.
  """

  pipeline_id = resolved_pipeline.get("pipelineId") or resolved_pipeline.get(
      "pipeline_id"
  )

  error_message_prefix = (
      f"Pipeline configuration for '{pipeline_id}' is invalid. Please address"
      " the following issues:\n"
  )

  from orchestration_pipelines_models.orchestration_pipelines_model import OrchestrationPipelinesModel  # pylint: disable=g-import-not-at-top
  try:
    OrchestrationPipelinesModel.build(resolved_pipeline)
  except ExceptionGroup as e:
    # Due to nested nature of validation exceptions for attrs classes, we need
    # to handle the error message aggregation manually.
    errors = _extract_nested_errors(e)
    error_message = "\n".join("  - " + error for error in errors)
    raise exceptions.Error(f"{error_message_prefix}{error_message}") from e
  except (ValueError, TypeError) as e:
    error_message = str(e)
    raise exceptions.Error(f"{error_message_prefix}{error_message}") from e


def _extract_nested_errors(exc: BaseException, path: str = "$") -> list[str]:
  """Recursively transforms validation exceptions into formatted error messages.

  If the exception contains nested exceptions (i.e., has an `exceptions`
  attribute), it traverses them to build a list of all errors. It uses
  `__notes__` attached to exceptions to construct a path to the error
  location (e.g., '$.field[0]').

  Args:
    exc: The validation exception, potentially containing nested exceptions.
    path: The current JSON-like path to the error location.

  Returns:
    A list of error strings, each formatted as "path: error message".
  """
  errors = []
  if not isinstance(exc, ExceptionGroup):
    errors.append(f"{path}: {str(exc)}")
    return errors

  excs_with_notes = []
  other_excs = []
  for subexc in exc.exceptions:
    note_found = False
    if hasattr(subexc, "__notes__"):
      for note in subexc.__notes__:
        if hasattr(note, "name") and hasattr(note, "type"):
          excs_with_notes.append((subexc, note))
          note_found = True
          break
        elif hasattr(note, "index") and hasattr(note, "type"):
          excs_with_notes.append((subexc, note))
          note_found = True
          break
    if not note_found:
      other_excs.append(subexc)

  for subexc, note in excs_with_notes:
    if hasattr(note, "name"):
      p = f"{path}.{note.name}"
    else:
      p = f"{path}[{note.index!r}]"

    if isinstance(subexc, ExceptionGroup):
      errors.extend(_extract_nested_errors(subexc, p))
    else:
      errors.append(f"{p}: {str(subexc)}")

  for subexc in other_excs:
    if isinstance(subexc, ExceptionGroup):
      errors.extend(_extract_nested_errors(subexc, path))
    else:
      errors.append(f"{path}: {str(subexc)}")
  return errors


def resolve_string_templates(yaml_content, variables):
  for key, value in variables.items():
    placeholder_pattern = r"{{\s*" + re.escape(key) + r"\s*}}"
    # Use a lambda to evaluate str(value) only if a match is found.
    # This allows passing objects that raise errors on __str__ conversion
    # to control when that error occurs (only if used).
    yaml_content = re.sub(
        placeholder_pattern, lambda m, v=value: str(v), yaml_content
    )
  return yaml_content


def check_for_missing_variables(content):
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

    # Extract resolved variables
    resolved_variables = {}
    env_dict = {}
    if (
        pre_deployment_yaml
        and ENVIRONMENTS_KEY in pre_deployment_yaml
        and env in pre_deployment_yaml[ENVIRONMENTS_KEY]
    ):
      env_dict = pre_deployment_yaml[ENVIRONMENTS_KEY][env]

    if VARIABLES_KEY in env_dict:
      # We need to revert the masking in the values of variables if they had any
      raw_vars = env_dict[VARIABLES_KEY] or {}
      for k, v in raw_vars.items():
        if isinstance(v, str):
          resolved_variables[k] = v.replace("__OPEN_TAG__", "{{").replace(
              "__CLOSE_TAG__", "}}"
          )
        else:
          resolved_variables[k] = v

    if external_variables:
      resolved_variables.update(external_variables)

    if SECRETS_KEY in env_dict:
      raw_secrets = env_dict[SECRETS_KEY] or {}
      if raw_secrets:
        sm_version = apis.ResolveVersion("secretmanager")
        client = apis.GetClientInstance("secretmanager", sm_version)
        messages = apis.GetMessagesModule("secretmanager", sm_version)
        for k, secret_name in raw_secrets.items():
          if k in resolved_variables:
            continue
          if isinstance(secret_name, str):
            secret_name = secret_name.replace("__OPEN_TAG__", "{{").replace(
                "__CLOSE_TAG__", "}}"
            )
            secret_name = resolve_string_templates(
                secret_name, resolved_variables
            )
          try:
            req = messages.SecretmanagerProjectsSecretsVersionsAccessRequest(
                name=secret_name
            )
            response = client.projects_secrets_versions.Access(req)
            resolved_variables[k] = response.payload.data.decode("utf-8")
          except Exception as e:
            raise BadFileError(
                f"Failed to fetch secret '{secret_name}' from Secret Manager:"
                f" {e}"
            ) from e

    # 3. Substitute on raw content
    resolved_content = resolve_string_templates(
        yaml_content, resolved_variables)

    check_for_missing_variables(resolved_content)

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
      environments[env], deployment_path, context=resolved_variables
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
  if getattr(environment, "variables", None):
    result["variables"] = environment.variables
  if getattr(environment, "secrets", None):
    result["secrets"] = environment.secrets

  return result


def collect_environment_variables() -> dict[str, str]:
  """Collects variables from environment variables with _DEPLOY_VAR_ prefix.

  Returns:
      A dictionary containing environment variables starting with
      _DEPLOY_VAR_ prefix.
  """
  env_vars = {}
  for key, value in os.environ.items():
    if key.startswith("_DEPLOY_VAR_"):
      env_vars[key[len("_DEPLOY_VAR_") :]] = value
  return env_vars


def validate_pipeline_l1(
    bundle_dir: pathlib.Path,
    environment: deployment_model.EnvironmentModel,
    combined_variables: Dict[str, Any] = None,
) -> None:
  """Syntax validation(L1) for the orchestration pipeline configuration."""

  for pipeline in environment.pipelines:
    pipeline_path = bundle_dir / pipeline.source

    try:
      yaml_content = files.ReadFileContents(pipeline_path)
    except files.Error as e:
      raise calliope_exceptions.BadFileException(
          f"Error reading {pipeline_path.name}: {e}"
      ) from e

    resolved_yaml_content = resolve_string_templates(
        yaml_content, combined_variables
    )
    check_for_missing_variables(resolved_yaml_content)

    try:
      resolved_yaml_content = yaml.load(resolved_yaml_content)
    except yaml.Error as e:
      raise calliope_exceptions.BadFileException(
          f"Failed to parse pipeline YAML after variable substitution: {e}"
      ) from e

    _build_orchestration_pipelines_model(resolved_yaml_content)
    log.status.Print(f"Successfully validated pipeline {pipeline.source}.")
