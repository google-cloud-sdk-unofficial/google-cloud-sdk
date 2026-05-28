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

from collections.abc import Mapping
import contextlib
import os
import pathlib
import re
import threading
from typing import Any, Dict, Iterable, Optional
from apitools.base.py import exceptions as apitools_exceptions
from cloudsdk.google.protobuf import descriptor_pb2
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.orchestration_pipelines import deployment_model
from googlecloudsdk.command_lib.orchestration_pipelines import git_context
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
from orchestration_pipelines_models.orchestration_pipelines_model import OrchestrationPipelinesModel


DEPLOYMENT_FILE_NAME = "deployment.yaml"
ARTIFACT_STORAGE_KEY = "artifact_storage"
ENVIRONMENTS_KEY = "environments"
VARIABLES_KEY = "variables"
SECRETS_KEY = "secrets"
RESOURCES_KEY = "resources"


class BadFileError(exceptions.Error):
  """Raised when the file is not valid."""

  pass


class InvalidPathError(exceptions.Error):
  """Raised when a path in the pipeline configuration is invalid."""

  pass


def resolve_dynamic_variables(
    yaml_content: str,
    combined_variables: Mapping[str, Any]
) -> Any:
  """Resolves dynamic variables in the YAML content.

  This function substitutes environment variables and other dynamic values
  into the provided YAML content.

  Args:
    yaml_content: The content of the YAML file to be resolved.
    combined_variables: Dict of combined variables to substitute.

  Returns:
    The resolved YAML content as a Python object (e.g., dict or list).
  """

  resolved_yaml_content = resolve_string_templates(
      yaml_content, combined_variables
  )
  try:
    parsed_yaml_content = yaml.load(resolved_yaml_content)
  except yaml.Error as e:
    raise BadFileError(
        f"Failed to parse pipeline YAML after variable substitution: {e}"
    ) from e
  if isinstance(parsed_yaml_content, dict) and "actions" in parsed_yaml_content:
    return _resolve_pipeline_yaml(parsed_yaml_content)
  return parsed_yaml_content


def _resolve_pipeline_yaml(
    yaml_content: Dict[str, Any]
) -> Dict[str, Any]:
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

    framework = action_props.get("framework", {})

    # Extract Local Upload Paths for Frameworks, SQL, and Python ---
    raw_upload_path = None

    if "dbt" in framework:
      raw_upload_path = (
          framework["dbt"]
          .get("airflowWorker", {})
          .get("projectDirectoryPath", "")
      )
    elif "dataform" in framework:
      raw_upload_path = (
          framework["dataform"]
          .get("airflowWorker", {})
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
        f"Error reading or parsing resource profile '{path}'"
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

      with allow_secret_resolution():
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


def _build_orchestration_pipelines_model(
    resolved_pipeline: Dict[str, Any],
) -> OrchestrationPipelinesModel:
  """Validates and builds a pipeline definition against a specific model version.

  This function extracts the 'model_version' from the provided definition,
  selects the corresponding Orchestration Pipelines model, and performs
  validation.

  Args:
    resolved_pipeline: The resolved pipeline definition as a dictionary.

  Returns:
    An instance of OrchestrationPipelinesModel.

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

  try:
    return OrchestrationPipelinesModel.build(resolved_pipeline)
  except Exception as e:
    if type(e).__name__ == "ParseError" or isinstance(
        e, (ValueError, TypeError)
    ):
      raise exceptions.Error(f"{error_message_prefix}{e}") from e
    raise


def _extract_paths_from_nested_proto(message: Any) -> list[str]:
  """Recursively extracts values from fields named 'path' within a proto message.

  Args:
    message: The proto message to traverse.

  Returns:
    A list of strings containing all values found in fields with "path" in
    their name.
  """
  if not hasattr(message, "ListFields"):
    return []

  exclude_fields = ["job", "properties", "project_directory_path"]
  values = []
  for field_descriptor, value in message.ListFields():
    field_name = field_descriptor.name

    if field_name in exclude_fields:
      continue

    if "path" in field_name.lower():
      if (
          field_descriptor.type
          == descriptor_pb2.FieldDescriptorProto.TYPE_STRING
      ):
        if (
            field_descriptor.label
            == descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED
        ):
          values.extend(value)
        else:
          values.append(value)

    if (
        field_descriptor.type
        == descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
    ):
      if (
          field_descriptor.label
          == descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED
      ):
        if field_descriptor.message_type.GetOptions().map_entry:
          value_descriptor = field_descriptor.message_type.fields_by_name[
              "value"
          ]
          # value is a dict {map_key: map_value}
          for map_key, map_val in value.items():
            # Check if the map key contains "path" and the value is a string
            if "path" in map_key.lower() and isinstance(map_val, str):
              values.append(map_val)

            # Check if the map value is a message and recurse
            if (
                value_descriptor.type
                == descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
            ):
              values.extend(_extract_paths_from_nested_proto(map_val))
        else:
          for element in value:
            values.extend(_extract_paths_from_nested_proto(element))
      else:
        values.extend(_extract_paths_from_nested_proto(value))
  return values


def _validate_gcp_project(project_id: str, pipeline_path: str):
  """Validates that a GCP project exists and is accessible.

  Checks if the provided `project_id` exists and if the current account has
  permissions to access it.

  Args:
    project_id: The GCP project ID to validate.
    pipeline_path: The relative path to the pipeline file for error messages.

  Raises:
    ValueError: If the project ID is missing.
    api_exceptions.HttpException: If the project is not found, inaccessible,
      or invalid, or for other HTTP errors during validation.
  """
  crm_version = apis.ResolveVersion("cloudresourcemanager")
  crm_message_module = apis.GetMessagesModule(
      "cloudresourcemanager", crm_version
  )
  resource_manager = apis.GetClientInstance("cloudresourcemanager", crm_version)
  if project_id:
    try:
      resource_manager.projects.Get(
          crm_message_module.CloudresourcemanagerProjectsGetRequest(
              projectId=project_id
          )
      )
    except apitools_exceptions.HttpForbiddenError as e:
      raise api_exceptions.HttpException(
          e,
          error_format=(
              f'Permission denied when checking GCP project "{project_id}" from'
              f' pipeline "{pipeline_path}". Please ensure your account has'
              " necessary permissions and the project exists."
          ),
      )
    except apitools_exceptions.HttpBadRequestError as e:
      raise api_exceptions.HttpException(
          e,
          error_format=(
              f'GCP project "{project_id}" from pipeline "{pipeline_path}" is'
              " invalid."
          ),
      )
    except apitools_exceptions.HttpError as e:
      raise api_exceptions.HttpException(
          e, error_format="Failed to check GCP project: {message}"
      )
  else:
    raise ValueError(
        f"No project ID is found for pipeline '{pipeline_path}'."
    )


def _validate_paths_in_pipeline(
    bundle_dir: pathlib.Path,
    pipeline_id: str,
    path_str: str,
):
  """Validates a path fields from a pipeline definition, checking for existence.

  Checks GCS object paths via API and local paths relative to the bundle
  directory.

  Args:
    bundle_dir: The directory where the pipeline bundle is located.
    pipeline_id: The pipeline ID for error messages.
    path_str: The path string to validate.

  Raises:
    InvalidPathError: If path_str is an invalid format, or points to a
      non-existent local or GCS resource.
    api_exceptions.HttpException: If permissions are insufficient during GCS
      path validation or for other HTTP errors.
  """
  if path_str.startswith("gs://"):
    version = apis.ResolveVersion("storage")
    client = apis.GetClientInstance("storage", version)
    messages = apis.GetMessagesModule("storage", version)
    storage_resource = None
    try:
      storage_resource = resources.REGISTRY.ParseStorageURL(path_str)
    except resources.WrongResourceCollectionException as e:
      raise InvalidPathError(
          f"Invalid GCS path in pipeline '{pipeline_id}': {path_str} - {e}"
      ) from e

    try:
      if not storage_resource.object:
        raise InvalidPathError(
            f"GCS path in pipeline '{pipeline_id}' appears to point to"
            f" a bucket '{path_str}' but an object path was expected."
        )
      client.objects.Get(
          messages.StorageObjectsGetRequest(
              bucket=storage_resource.bucket, object=storage_resource.object
          )
      )
    except apitools_exceptions.HttpForbiddenError as e:
      raise api_exceptions.HttpException(
          e,
          error_format=(
              f'Permission denied when checking GCS path "{path_str}" in'
              f' pipeline "{pipeline_id}". Please ensure your account has'
              " necessary permissions."
          ),
      )
    except apitools_exceptions.HttpNotFoundError as e:
      raise api_exceptions.HttpException(
          e,
          error_format=(
              f'GCS path "{path_str}" from pipeline "{pipeline_id}" does'
              " not exist."
          ),
      )
    except apitools_exceptions.HttpBadRequestError as e:
      raise api_exceptions.HttpException(
          e,
          error_format=(
              f'GCS path "{path_str}" from pipeline "{pipeline_id}" is invalid.'
          ),
      )
    except apitools_exceptions.HttpError as e:
      raise api_exceptions.HttpException(
          e, error_format="Failed to check GCS path: {message}"
      )
  elif not path_str.startswith(("http://", "https://", "/")):
    candidate_path = bundle_dir / path_str
    if not candidate_path.exists():
      raise InvalidPathError(
          f"In pipeline '{pipeline_id}', path '{path_str}' does not "
          f"exist relative to bundle directory: {candidate_path}"
      )
  else:
    raise InvalidPathError(
        f"Invalid path in pipeline '{pipeline_id}': {path_str}"
    )


def _validate_composer_environment(
    composer_environment_resource_name: str, pipeline_id: str
):
  """Validates that a Composer environment exists.

  Args:
    composer_environment_resource_name: The Composer environment resource name
      to validate.
    pipeline_id: The pipeline ID for error messages.

  Raises:
    api_exceptions.HttpException: If the Composer environment is not found,
      inaccessible, or invalid, or for other HTTP errors during validation.
  """
  version = apis.ResolveVersion("composer")
  composer_message_module = apis.GetMessagesModule("composer", version)
  composer = apis.GetClientInstance("composer", version)
  try:
    composer.projects_locations_environments.Get(
        composer_message_module.ComposerProjectsLocationsEnvironmentsGetRequest(
            name=composer_environment_resource_name
        )
    )
  except apitools_exceptions.HttpForbiddenError as e:
    raise api_exceptions.HttpException(
        e,
        error_format=(
            "Permission denied when checking Composer environment"
            f' "{composer_environment_resource_name}" from pipeline'
            f' "{pipeline_id}". Please ensure your account has necessary'
            " permissions and the Composer environment exists."
        ),
    )
  except apitools_exceptions.HttpNotFoundError as e:
    raise api_exceptions.HttpException(
        e,
        error_format=(
            f'Composer environment "{composer_environment_resource_name}"'
            f' from pipeline "{pipeline_id}" does not exist.'
        ),
    )
  except apitools_exceptions.HttpBadRequestError as e:
    raise api_exceptions.HttpException(
        e,
        error_format=(
            f'Composer environment "{composer_environment_resource_name}"'
            f' from pipeline "{pipeline_id}" is invalid.'
        ),
    )
  except apitools_exceptions.HttpError as e:
    raise api_exceptions.HttpException(
        e, error_format="Failed to check Composer environment: {message}"
    )


def _validate_dataproc_cluster(
    cluster_name: str,
    region: str,
    project_id: str,
    action_name: str,
    pipeline_id: str,
):
  """Validates that a Dataproc cluster exists.

  Args:
    cluster_name: The Dataproc cluster name to validate.
    region: The region of the cluster.
    project_id: The project ID of the cluster.
    action_name: The name of the action for error messages.
    pipeline_id: The pipeline ID for error messages.

  Raises:
    api_exceptions.HttpException: If the Dataproc cluster is not found,
      inaccessible, or invalid, or for other HTTP errors during validation.
  """
  version = apis.ResolveVersion("dataproc")
  dataproc_message_module = apis.GetMessagesModule("dataproc", version)
  dataproc = apis.GetClientInstance("dataproc", version)
  try:
    dataproc.projects_regions_clusters.Get(
        dataproc_message_module.DataprocProjectsRegionsClustersGetRequest(
            clusterName=cluster_name, region=region, projectId=project_id
        )
    )
  except apitools_exceptions.HttpForbiddenError as e:
    raise api_exceptions.HttpException(
        e,
        error_format=(
            "Permission denied when checking Dataproc cluster"
            f' "{cluster_name}" from pipeline "{pipeline_id}" and action'
            f' "{action_name}". Please ensure'
            " your account has necessary permissions and the cluster exists."
        ),
    )
  except apitools_exceptions.HttpNotFoundError as e:
    raise api_exceptions.HttpException(
        e,
        error_format=(
            f'Dataproc cluster "{cluster_name}" from pipeline'
            f' "{pipeline_id}" and action "{action_name}" does not exist.'
        ),
    )
  except apitools_exceptions.HttpBadRequestError as e:
    raise api_exceptions.HttpException(
        e,
        error_format=(
            f'Dataproc cluster "{cluster_name}" from pipeline'
            f' "{pipeline_id}" and action "{action_name}" is invalid.'
        ),
    )
  except apitools_exceptions.HttpError as e:
    raise api_exceptions.HttpException(
        e, error_format="Failed to check Dataproc cluster: {message}"
    )


_SECRET_RESOLUTION_ALLOWED = threading.local()


class SecretValue:
  """A wrapper for secret values that fails on __str__ unless allowed."""

  def __init__(self, value: str):
    self._value = value

  def __str__(self) -> str:
    if getattr(_SECRET_RESOLUTION_ALLOWED, "value", False):
      return self._value
    raise ValueError(
        "Secret value cannot be converted to string in this context."
    )


@contextlib.contextmanager
def allow_secret_resolution():
  """Context manager to allow SecretValue to be converted to string."""
  old_value = getattr(_SECRET_RESOLUTION_ALLOWED, "value", False)
  _SECRET_RESOLUTION_ALLOWED.value = True
  try:
    yield
  finally:
    _SECRET_RESOLUTION_ALLOWED.value = old_value


def resolve_string_templates(
    yaml_content: str, variables: Mapping[str, Any]
) -> str:
  """Resolves template variables in a string."""
  for key, value in variables.items():
    placeholder_pattern = (
        r"(?:{{\s*|__OPEN_TAG__\s*)"
        + re.escape(key)
        + r"(?:\s*}}|\s*__CLOSE_TAG__)"
    )
    # Use a lambda to evaluate str(value) only if a match is found.
    # This allows passing objects that raise errors on __str__ conversion
    # to control when that error occurs (only if used).
    yaml_content = re.sub(
        placeholder_pattern, lambda m, v=value: str(v), yaml_content
    )
  return yaml_content


def check_for_missing_variables(
    content: str, allowed_missing: Iterable[str] = ()
) -> None:
  """Checks if there are any unsubstituted variables in the content."""
  pattern = r"{{\s*([A-Za-z0-9_]+)\s*}}"

  matches = re.finditer(pattern, content)
  for match in matches:
    var_name = match.group(1)
    if var_name not in allowed_missing:
      raise BadFileError(
          f"Variable '{var_name}' is not resolved in the content. Please ensure"
          " that all variables are defined using deployment file, environment"
          " variables, or substitutions argument."
      )


def load_all_environments(
    deployment_path: str,
    external_variables: Optional[Dict[str, Any]] = None,
) -> tuple[Dict[str, deployment_model.EnvironmentModel], Dict[str, Any]]:
  """Lists all deployment environments configuration."""
  yaml_content, pre_deployment_yaml = _get_pre_deployment_data(deployment_path)

  environments = pre_deployment_yaml.get(ENVIRONMENTS_KEY)
  if isinstance(environments, Mapping):
    all_environments = {}
    failed_environments = {}
    for env in environments.keys():
      try:
        all_environments[env] = _load_environment_from_pre_parsed(
            deployment_path,
            yaml_content,
            pre_deployment_yaml,
            env,
            external_variables,
        )
      except BadFileError as e:
        failed_environments[env] = e
    return all_environments, failed_environments
  return {}, {}


def load_environment(
    deployment_path: str,
    env: str,
    external_variables: Optional[Dict[str, Any]] = None,
) -> deployment_model.EnvironmentModel:
  """Loads the deployment environment configuration."""
  yaml_content, pre_deployment_yaml = _get_pre_deployment_data(deployment_path)
  return _load_environment_from_pre_parsed(
      deployment_path,
      yaml_content,
      pre_deployment_yaml,
      env,
      external_variables,
  )


def collect_external_vars(
    args: Any, bundle_path: pathlib.Path
) -> Dict[str, Any]:
  """Collects external variables from environment, file, and args."""
  external_vars = {}
  substitutions_file_vars = {}
  if getattr(args, "substitutions_file", None):
    try:
      substitutions_file_vars = yaml.load_path(args.substitutions_file)
      if not isinstance(substitutions_file_vars, dict):
        raise calliope_exceptions.BadFileException(
            f"Substitutions file {args.substitutions_file} "
            "must contain a dictionary."
        )
    except yaml.Error as e:
      raise calliope_exceptions.BadFileException(
          f"Error parsing substitutions file {args.substitutions_file}: {e}"
      ) from e

  env_vars = collect_environment_variables()
  external_vars.update(env_vars)
  external_vars.update(substitutions_file_vars)

  substitutions = getattr(args, "substitutions", None)
  if substitutions:
    external_vars.update(substitutions)

  # 4. Collect special values (COMMIT_SHA)
  if getattr(args, "rollback", False) and getattr(args, "version", None):
    if "COMMIT_SHA" in external_vars:
      log.warning(
          "Both --version and COMMIT_SHA provided. COMMIT_SHA will be"
          " ignored in favor of --version for rollback."
      )
    external_vars["COMMIT_SHA"] = args.version

  if "COMMIT_SHA" not in external_vars:

    external_vars["COMMIT_SHA"] = git_context.SafeCommitSha.CreateLazy(
        bundle_path=bundle_path,
        is_local=getattr(args, "local", False),
    )

  return external_vars


def add_substitution_flags(parser: Any) -> None:
  """Adds --substitutions and --substitutions-file flags to the parser."""
  parser.add_argument(
      "--substitutions",
      metavar="KEY=VALUE",
      type=arg_parsers.ArgDict(),
      help="Variables to substitute in the pipeline configuration.",
  )
  parser.add_argument(
      "--substitutions-file",
      help=(
          "Path to a YAML file containing variable substitutions for the "
          "pipeline configuration."
      ),
  )


def load_environment_with_args(args: Any) -> deployment_model.EnvironmentModel:
  """Loads the environment configuration based on command-line arguments."""
  bundle_path = pathlib.Path.cwd()
  external_vars = collect_external_vars(args, bundle_path)
  deployment_path = bundle_path / DEPLOYMENT_FILE_NAME
  return load_environment(str(deployment_path), args.environment, external_vars)


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
) -> tuple[Dict[str, Any], Dict[str, Any], deployment_model.EnvironmentModel]:
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

  combined_variables = {
      "project": result.get("project"),
      "region": result.get("region"),
      **result.get("variables", {}),
  }

  return result, combined_variables, environment


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


def _extract_resource_profile_paths(config: Any) -> list[str]:
  """Recursively extracts resource profile paths from a pipeline config."""
  paths = []
  if isinstance(config, dict):
    for k, v in config.items():
      if k == "resourceProfile" and isinstance(v, dict) and "path" in v:
        paths.append(v["path"])
      else:
        paths.extend(_extract_resource_profile_paths(v))
  elif isinstance(config, list):
    for item in config:
      paths.extend(_extract_resource_profile_paths(item))
  return paths


def validate_pipeline_l1(
    bundle_dir: pathlib.Path,
    pipeline_paths: list[str],
    combined_variables: Optional[Mapping[str, Any]] = None,
    secret_keys: Iterable[str] = (),
    allowed_missing: Iterable[str] = (),
) -> list[OrchestrationPipelinesModel]:
  """Performs L1 validation for all pipelines in an environment.

  L1 validation includes syntax checking, variable substitution, and
  validation against the orchestration pipelines data model.

  Args:
    bundle_dir: The directory where pipeline bundles are located.
    pipeline_paths: The list of pipeline file paths to validate.
    combined_variables: Dictionary of variables for template substitution.
    secret_keys: Optional list of secret keys to check against.
    allowed_missing: Optional list of variables allowed to be missing.

  Returns:
    A list of `OrchestrationPipelinesModel` instances for the validated
    pipelines.

  Raises:
    BadFileError: If a pipeline file cannot be read or parsed, or if variable
    substitution fails, or if secrets are used.
    exceptions.Error: If model validation fails.
  """
  pipeline_models = []
  for pipeline_path in pipeline_paths:
    full_pipeline_path = bundle_dir / pipeline_path

    try:
      yaml_content = files.ReadFileContents(full_pipeline_path)
    except files.Error as e:
      raise BadFileError(f"Error reading {full_pipeline_path}: {e}") from e

    resolved_yaml_content = resolve_string_templates(
        yaml_content, combined_variables or {}
    )

    if secret_keys:
      for key in secret_keys:
        pattern = r"{{\s*" + re.escape(key) + r"\s*}}"
        if re.search(pattern, resolved_yaml_content):
          raise BadFileError(
              "Secrets are only supported in the resources section of "
              "deployment.yaml, but found secret reference "
              f"'{{{{ {key} }}}}' in pipeline file {pipeline_path}."
          )

    check_for_missing_variables(resolved_yaml_content, allowed_missing)

    try:
      resolved_pipeline = yaml.load(resolved_yaml_content)
    except yaml.Error as e:
      raise BadFileError(
          f"Failed to parse pipeline YAML after variable substitution: {e}"
      ) from e

    profile_paths = _extract_resource_profile_paths(resolved_pipeline)
    for pp in profile_paths:
      if not pp.startswith(("gs://", "/")):
        full_pp = bundle_dir / pp
        if full_pp.exists():
          try:
            profile_content = files.ReadFileContents(full_pp)
            if secret_keys:
              for key in secret_keys:
                pattern = r"{{\s*" + re.escape(key) + r"\s*}}"
                if re.search(pattern, profile_content):
                  raise BadFileError(
                      "Secrets are only supported in the resources section of "
                      "deployment.yaml, but found secret reference "
                      f"'{{{{ {key} }}}}' in resource profile {pp} "
                      f"referenced by pipeline {pipeline_path}."
                  )
          except files.Error:
            pass

    pipeline_models.append(
        _build_orchestration_pipelines_model(resolved_pipeline)
    )

    # Check if pipeline ID matches pipeline file name
    pipeline_id = resolved_pipeline.get("pipelineId") or resolved_pipeline.get(
        "pipeline_id"
    )
    pipeline_stem = pathlib.Path(pipeline_path).stem
    if pipeline_id != pipeline_stem:
      raise BadFileError(
          f"Pipeline ID {pipeline_id!r} does not match pipeline file name"
          f" {pathlib.Path(pipeline_path).stem!r} in {pipeline_path!r}."
      )

  return pipeline_models


def _get_pre_deployment_data(
    deployment_path: str,
) -> tuple[str, Optional[Dict[str, Any]]]:
  """Reads, masks, and partially parses the deployment YAML.

  We mask jinja2-style templates {{ ... }} to make it valid YAML for the
  first pass. We replace {{ with __OPEN_TAG__ and }} with __CLOSE_TAG__
  so that "name: {{ VAR }}" becomes
  "name: __OPEN_TAG__ VAR __CLOSE_TAG__" which is a valid string.

  Args:
    deployment_path: The path to the deployment file.

  Returns:
    A tuple containing the raw YAML content and the pre-parsed YAML dictionary.

  Raises:
    BadFileError: If the file cannot be read or parsed.
  """
  try:
    yaml_content = files.ReadFileContents(deployment_path)
    masked_content = yaml_content.replace("{{", "__OPEN_TAG__").replace(
        "}}", "__CLOSE_TAG__"
    )
    pre_deployment_yaml = yaml.load(masked_content)
    return yaml_content, pre_deployment_yaml
  except (IOError, OSError, yaml.Error) as e:
    raise BadFileError(f"Error reading or parsing deployment.yaml: {e}") from e


def _contains_secret_reference(value: Any, secret_keys: Iterable[str]) -> bool:
  """Checks if a value contains a reference to any of the secrets."""
  if isinstance(value, str):
    for key in secret_keys:
      pattern = r"__OPEN_TAG__\s*" + re.escape(key) + r"\s*__CLOSE_TAG__"
      if re.search(pattern, value):
        return True
  elif isinstance(value, dict):
    return any(
        _contains_secret_reference(v, secret_keys) for v in value.values()
    )
  elif isinstance(value, list):
    return any(_contains_secret_reference(v, secret_keys) for v in value)
  return False


def resolve_templates_in_dict(data: Any, variables: Mapping[str, Any]) -> Any:
  """Recursively resolves string templates in a dictionary or list."""
  if isinstance(data, str):
    return resolve_string_templates(data, variables)
  elif isinstance(data, dict):
    return {
        k: resolve_templates_in_dict(v, variables) for k, v in data.items()
    }
  elif isinstance(data, list):
    return [resolve_templates_in_dict(v, variables) for v in data]
  return data


def _find_unresolved_variables(data: Any) -> list[str]:
  """Recursively finds masked unresolved variables in a dict or list."""
  unresolved = []
  if isinstance(data, str):
    # Matches any characters between __OPEN_TAG__ and __CLOSE_TAG__,
    # allowing for variable names with special characters like hyphens.
    matches = re.findall(r"__OPEN_TAG__\s*(.*?)\s*__CLOSE_TAG__", data)
    unresolved.extend(matches)
  elif isinstance(data, dict):
    for v in data.values():
      unresolved.extend(_find_unresolved_variables(v))
  elif isinstance(data, list):
    for v in data:
      unresolved.extend(_find_unresolved_variables(v))
  return unresolved


def _load_environment_from_pre_parsed(
    deployment_path: str,
    yaml_content: str,
    pre_deployment_yaml: Optional[Dict[str, Any]],
    env: str,
    external_variables: Optional[Dict[str, Any]] = None,
) -> deployment_model.EnvironmentModel:
  """Loads a specific environment configuration from pre-parsed content."""
  if not pre_deployment_yaml or ENVIRONMENTS_KEY not in pre_deployment_yaml:
    raise BadFileError("Error parsing deployment file: no environments found.")

  if env not in pre_deployment_yaml[ENVIRONMENTS_KEY]:
    raise BadFileError(f"Environment '{env}' not found in deployment file.")

  env_dict = pre_deployment_yaml[ENVIRONMENTS_KEY][env]
  if not isinstance(env_dict, dict):
    raise BadFileError(
        f"Environment '{env}' configuration must be a dictionary."
    )

  # Extract resolved variables
  resolved_variables = {}
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

  raw_secrets = {}
  if SECRETS_KEY in env_dict:
    raw_secrets = env_dict[SECRETS_KEY] or {}

  # Prevent recursive workarounds
  if VARIABLES_KEY in env_dict:
    raw_vars = env_dict[VARIABLES_KEY] or {}
    if _contains_secret_reference(raw_vars, raw_secrets.keys()):
      raise BadFileError("Variables cannot reference secrets.")

  # Enforce secrets only in resources
  for key, value in env_dict.items():
    if key == "resources":
      continue
    if _contains_secret_reference(value, raw_secrets.keys()):
      raise BadFileError(
          "Secrets are only supported in the resources section, but found in "
          f"section '{key}'."
      )

  secret_variables = {}
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
        secret_variables[k] = SecretValue(response.payload.data.decode("utf-8"))
      except Exception as e:
        raise BadFileError(
            f"Failed to fetch secret '{secret_name}' from Secret Manager: {e}"
        ) from e

  # Extract captured variables to allow them to be missing in initial validation
  captured_vars = set()
  resources_def = env_dict.get("resources", [])
  for r in resources_def:
    if isinstance(r, dict):
      capture_defs = r.get("capture", [])
      for c in capture_defs:
        if isinstance(c, dict) and "variable" in c:
          captured_vars.add(c["variable"])

  # 3. Substitute on raw content (only non-secret variables)
  resolved_content = resolve_string_templates(
      yaml_content, resolved_variables
  )

  check_for_missing_variables(
      resolved_content,
      allowed_missing=list(raw_secrets.keys()) + list(captured_vars),
  )

  # Mask unresolved secrets and captured variables to make it valid YAML
  masked_for_yaml = resolved_content
  for key in list(raw_secrets.keys()) + list(captured_vars):
    pattern = r"{{\s*" + re.escape(key) + r"\s*}}"
    masked_for_yaml = re.sub(
        pattern, f"__OPEN_TAG__ {key} __CLOSE_TAG__", masked_for_yaml
    )

  # 4. Final Parse
  try:
    deployment_yaml = yaml.load(masked_for_yaml)
  except yaml.Error as e:
    raise BadFileError(f"Error parsing deployment.yaml: {e}") from e

  # Resolve secrets in resources section of deployment_yaml
  if (
      "environments" in deployment_yaml
      and env in deployment_yaml["environments"]
  ):
    env_data = deployment_yaml["environments"][env]
    if "resources" in env_data:
      with allow_secret_resolution():
        env_data["resources"] = resolve_templates_in_dict(
            env_data["resources"], {**resolved_variables, **secret_variables}
        )

  deployment_yaml["environments"][env]["secrets"] = secret_variables

  try:
    deployment = deployment_model.DeploymentModel.build(deployment_yaml)
  except (KeyError, TypeError, ValueError, AttributeError) as e:
    raise BadFileError(f"Error parsing deployment configuration: {e}") from e

  env_model = deployment.environments[env]
  available_vars = set(resolved_variables.keys()) | set(secret_variables.keys())

  for resource in env_model.resources:
    if isinstance(resource, deployment_model.ResourceModel):
      unresolved = []
      if resource.definition:
        unresolved.extend(_find_unresolved_variables(resource.definition))
      if resource.name:
        unresolved.extend(_find_unresolved_variables(resource.name))
      if resource.parent:
        unresolved.extend(_find_unresolved_variables(resource.parent))

      for var in unresolved:
        if var not in available_vars:
          raise BadFileError(
              f"Resource '{resource.name}' uses variable '{var}' "
              "before it is defined or captured."
          )
      # Add captured variables to available_vars
      for c in resource.capture:
        available_vars.add(c.variable)

  environments = getattr(deployment, ENVIRONMENTS_KEY)
  if env not in environments:
    raise BadFileError(f"Environment '{env}' not found in deployment file.")

  # Expand resources after building the model
  _expand_environment_resources(
      environments[env],
      deployment_path,
      context={**resolved_variables, **secret_variables},
  )

  return environments[env]


def _validate_single_pipeline(
    pipeline_model: OrchestrationPipelinesModel,
    bundle_dir: pathlib.Path,
    environment: deployment_model.EnvironmentModel,
) -> None:
  """Performs L2 semantic validation for a single orchestration pipeline.

  L2 validation includes checks requiring external calls, such as verifying
  GCP project existence and path (local or GCS) validity.

  Args:
    pipeline_model: The OrchestrationPipelinesModel object to validate.
    bundle_dir: The directory where pipeline bundles are located.
    environment: The deployment_model.EnvironmentModel object.

  Raises:
    BadFileError: If a pipeline file cannot be read or parsed, or if variable
      substitution fails.
    InvalidPathError: If any path in the pipeline is invalid.
    api_exceptions.HttpException: If GCP project or GCS path validation fails
      due to API errors.
  """
  project = pipeline_model.defaults.project_id
  region = pipeline_model.defaults.location
  # Check if GCP project exists
  _validate_gcp_project(project, pipeline_model.pipeline_id)

  # Check if all 'path' fields refer to existing resources.
  all_paths_in_pipeline = _extract_paths_from_nested_proto(pipeline_model)
  for path_str in all_paths_in_pipeline:
    _validate_paths_in_pipeline(
        bundle_dir, pipeline_model.pipeline_id, path_str
    )

  # Check if Composer environment exists
  if environment:
    if not environment.composer_environment:
      raise BadFileError(
          "Composer environment name is not set in deployment file."
      )
    composer_environment_resource_name = f"projects/{environment.project}/locations/{environment.region}/environments/{environment.composer_environment}"
    _validate_composer_environment(
        composer_environment_resource_name, pipeline_model.pipeline_id
    )

  # Check if specified Dataproc cluster exists
  for action in pipeline_model.actions:
    if (
        action.WhichOneof("action") == "pyspark"
        and action.pyspark.engine.WhichOneof("engine") == "dataproc_on_gce"
        and action.pyspark.engine.dataproc_on_gce.WhichOneof("config")
        == "existing_cluster"
    ):
      pyspark_action = action.pyspark
      existing_cluster = pyspark_action.engine.dataproc_on_gce.existing_cluster
      cluster_region = existing_cluster.location or region
      cluster_project = existing_cluster.project_id or project
      if not cluster_region:
        raise BadFileError(
            "Region is not set in Dataproc cluster config or pipeline defaults."
        )
      if not cluster_project:
        raise BadFileError(
            "Project is not set in Dataproc cluster config or pipeline"
            " defaults."
        )
      _validate_dataproc_cluster(
          existing_cluster.cluster_name,
          cluster_region,
          cluster_project,
          pyspark_action.name,
          pipeline_model.pipeline_id,
      )


def validate_pipeline_l2(
    bundle_dir: pathlib.Path,
    pipeline_models: Iterable[OrchestrationPipelinesModel],
    environment: Optional[deployment_model.EnvironmentModel] = None,
) -> None:
  """Performs L2 validation for all pipelines in the deployment environment."""

  for pipeline_model in pipeline_models:
    _validate_single_pipeline(pipeline_model, bundle_dir, environment)
