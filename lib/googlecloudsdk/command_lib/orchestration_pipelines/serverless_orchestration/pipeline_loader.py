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
"""Loads a Serverless Orchestration pipeline YAML and its environment settings."""

import argparse
from collections.abc import Mapping, Sequence
import dataclasses
import os
import pathlib
import re
from typing import Any

from googlecloudsdk.command_lib.orchestration_pipelines import deployment_model
from googlecloudsdk.command_lib.orchestration_pipelines.serverless_orchestration import errors
from googlecloudsdk.command_lib.orchestration_pipelines.tools import yaml_processor
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

ORCHESTRATION_SERVICE_RUNNER = "orchestration_service"
DEFAULT_PIPELINE_FILE_NAME = "pipeline.yaml"

_OPEN_TAG_MASK = "__OPEN_TAG__"
_CLOSE_TAG_MASK = "__CLOSE_TAG__"
_TEMPLATE_TAG_RE = re.compile(r"\{\{(.*?)\}\}")


@dataclasses.dataclass(frozen=True)
class DbtAction:
  """Configuration for a dbt action in a Serverless Orchestration pipeline."""

  name: str
  # Absolute path of the dbt project directory.
  project_directory: pathlib.Path
  # Version of the Google-managed dbt runtime, e.g. `1.9`.
  dbt_version: str
  command: str = "build"
  select: tuple[str, ...] = ()
  variables: Mapping[str, Any] = dataclasses.field(default_factory=dict)
  # Literal `profileConfig` values, rendered into `profiles.yml` when packaging.
  profile_config: Mapping[str, Any] = dataclasses.field(default_factory=dict)
  full_refresh: bool = False


@dataclasses.dataclass(frozen=True)
class LoadedPipeline:
  """Validated pipeline configuration and target environment settings."""

  pipeline_id: str
  project: str
  location: str
  # The deployment environment (`--environment`); also the dbt target name.
  target: str
  # Email of the service account the pipeline runs as, when configured.
  service_account: str | None
  # Bucket name without `gs://`, from `deployment.yaml` `artifact_storage` or
  # the `dcs-artifacts-<projectNumber>-<location>` default.
  artifact_bucket: str
  base_dir: pathlib.Path
  actions: tuple[DbtAction, ...]
  # `artifact_storage.path_prefix` of `deployment.yaml`; empty when not set.
  artifact_path_prefix: str = ""


@dataclasses.dataclass(frozen=True)
class ResolvedPipeline:
  """Selected pipeline YAML file and its parsed contents."""

  pipeline_file_path: pathlib.Path
  raw_pipeline_yaml: Mapping[str, Any]
  # Path to `deployment.yaml`, or None when `./pipeline.yaml` was used.
  deployment_file_path: pathlib.Path | None


def LoadRawYamlMapping(file_path: pathlib.Path) -> Mapping[str, Any]:
  """Loads a YAML mapping, masking `{{ }}` template tags before parsing.

  Args:
    file_path: Path to the YAML file to read.

  Returns:
    The parsed top-level YAML mapping.

  Raises:
    errors.PipelineLoadError: If the file cannot be read, is not valid YAML, or
      does not parse to a mapping.
  """
  try:
    file_content = files.ReadFileContents(str(file_path))
    # Unquoted `{{ var }}` template tags parse as nested YAML flow mappings
    # (`{"var": None}`), so mask `{{` and `}}` before parsing.
    file_content = _TEMPLATE_TAG_RE.sub(
        f"{_OPEN_TAG_MASK}\\1{_CLOSE_TAG_MASK}", file_content
    )
    yaml_mapping = yaml.load(file_content)
  except (files.Error, UnicodeDecodeError, yaml.Error) as e:
    raise errors.PipelineLoadError(f"Failed to load '{file_path}': {e}") from e
  if not isinstance(yaml_mapping, Mapping):
    raise errors.PipelineLoadError(f"Expected a YAML mapping in '{file_path}'.")
  return yaml_mapping


def GetPipelineFilePaths(
    environment_name: str | None = None,
) -> list[pathlib.Path]:
  """Returns the `pipelines[].source` paths or `[./pipeline.yaml]`.

  Args:
    environment_name: The target deployment environment (`--environment`), or
      None when omitted.

  Returns:
    The candidate pipeline YAML file paths for the deployment.

  Raises:
    errors.PipelineLoadError: If `deployment.yaml` is invalid.
  """
  _, pipeline_file_paths = _GetDeploymentAndPipelineFilePaths(environment_name)
  return pipeline_file_paths or [_GetDefaultPipelineFilePath()]


def GetPipeline(args: argparse.Namespace) -> ResolvedPipeline:
  """Finds and parses the pipeline YAML selected by `args`.

  When `./deployment.yaml` is present for `--environment`, selects the matching
  `pipelines[].source` entry (or `./pipeline.yaml` if `pipelines` is empty).
  When `./deployment.yaml` is absent, uses `--pipeline` or `./pipeline.yaml`.

  Args:
    args: The parsed command-line arguments.

  Returns:
    The resolved pipeline path, parsed YAML mapping, and `deployment.yaml` path.

  Raises:
    errors.PipelineLoadError: If a YAML file is unreadable or malformed.
    errors.AmbiguousPipelineError: If `deployment.yaml` lists multiple pipelines
      and `--pipeline` is omitted.
  """
  deployment_file_path, pipeline_file_paths = (
      _GetDeploymentAndPipelineFilePaths(args.environment)
  )
  pipeline_file_path = _SelectPipelineFilePath(
      args, deployment_file_path, pipeline_file_paths
  )
  return ResolvedPipeline(
      pipeline_file_path=pipeline_file_path,
      raw_pipeline_yaml=LoadRawYamlMapping(pipeline_file_path),
      deployment_file_path=deployment_file_path,
  )


def LoadPipeline(args: argparse.Namespace) -> LoadedPipeline:
  """Loads and validates the pipeline YAML selected by `args`.

  Args:
    args: The parsed command-line arguments.

  Returns:
    The validated pipeline model merged with its target environment.

  Raises:
    errors.PipelineLoadError: If the pipeline or environment config is invalid.
    errors.AmbiguousPipelineError: If `deployment.yaml` lists multiple pipelines
      and `--pipeline` is omitted.
  """
  resolved_pipeline = GetPipeline(args)
  _VerifyNoTemplateTags(resolved_pipeline)
  raw_pipeline_yaml = resolved_pipeline.raw_pipeline_yaml
  pipeline_file_path = resolved_pipeline.pipeline_file_path
  source_description = f"Pipeline '{pipeline_file_path}'"
  environment_name = args.environment
  pipeline_id = _GetNonEmptyStringFromMapping(
      raw_pipeline_yaml, "pipelineId", source_description
  )
  defaults = _GetTypedFieldFromMapping(
      raw_pipeline_yaml, "defaults", Mapping, source_description, default={}
  )
  dbt_action = _GetDbtActionFromPipelineYaml(
      raw_pipeline_yaml.get("actions"), pipeline_file_path.parent
  )
  environment = _GetEnvironmentModelFromDeploymentFile(
      args, resolved_pipeline.deployment_file_path
  )
  project = _GetProjectId(environment, defaults, source_description)
  location = _GetLocation(environment, defaults, source_description)
  artifact_bucket, artifact_path_prefix = _GetArtifactBucketAndPathPrefix(
      environment, project, location
  )
  return LoadedPipeline(
      pipeline_id=pipeline_id,
      project=project,
      location=location,
      target=environment_name or "default",
      service_account=_GetServiceAccountEmail(
          environment, defaults, source_description
      ),
      artifact_bucket=artifact_bucket,
      base_dir=pipeline_file_path.parent,
      actions=(dbt_action,),
      artifact_path_prefix=artifact_path_prefix,
  )


def _GetDeploymentAndPipelineFilePaths(
    environment_name: str | None,
) -> tuple[pathlib.Path | None, list[pathlib.Path]]:
  """Returns `(deployment_file_path, pipeline_file_paths)` for `environment_name`."""
  deployment_file_path = _GetDeploymentFilePath(environment_name)
  if deployment_file_path is None or not environment_name:
    return None, []
  return (
      deployment_file_path,
      _GetPipelineFilePathsFromDeploymentFile(
          deployment_file_path, environment_name
      ),
  )


def _GetDeploymentFilePath(
    environment_name: str | None,
) -> pathlib.Path | None:
  """Returns `./deployment.yaml` when present and `environment_name` is set."""
  if not environment_name:
    return None
  deployment_file_path = (
      pathlib.Path.cwd() / yaml_processor.DEPLOYMENT_FILE_NAME
  )
  if deployment_file_path.is_file():
    return deployment_file_path
  return None


def _GetPipelineFilePathsFromDeploymentFile(
    deployment_file_path: pathlib.Path, environment_name: str
) -> list[pathlib.Path]:
  """Returns resolved `pipelines[].source` paths of `environment_name`."""
  environment_config = _GetEnvironmentConfigFromDeploymentFile(
      deployment_file_path, environment_name
  )
  location_description = (
      f"environment '{environment_name}' in '{deployment_file_path}'"
  )
  pipeline_entries = environment_config.get("pipelines")
  if pipeline_entries is None:
    return []
  if not isinstance(pipeline_entries, list):
    raise errors.PipelineLoadError(
        f"`pipelines` of {location_description} must be a list."
    )
  return [
      deployment_file_path.parent
      / _GetPipelineFilePathFromPipelineEntry(
          pipeline_entry, location_description
      )
      for pipeline_entry in pipeline_entries
  ]


def _GetEnvironmentConfigFromDeploymentFile(
    deployment_file_path: pathlib.Path, environment_name: str
) -> Mapping[str, Any]:
  """Returns the validated `environments[environment_name]` mapping."""
  deployment_yaml = LoadRawYamlMapping(deployment_file_path)
  environments = deployment_yaml.get(yaml_processor.ENVIRONMENTS_KEY)
  if (
      not isinstance(environments, Mapping)
      or environment_name not in environments
  ):
    raise errors.PipelineLoadError(
        f"Environment '{environment_name}' not found in"
        f" '{deployment_file_path}'."
    )
  environment_config = environments[environment_name]
  if not isinstance(environment_config, Mapping):
    raise errors.PipelineLoadError(
        f"Environment '{environment_name}' in '{deployment_file_path}' must be"
        " a mapping."
    )
  return environment_config


def _GetPipelineFilePathFromPipelineEntry(
    pipeline_entry: Any, location_description: str
) -> str:
  """Returns the non-blank `source` of one `pipelines` entry."""
  pipeline_file_path = (
      pipeline_entry.get("source")
      if isinstance(pipeline_entry, Mapping)
      else None
  )
  if not isinstance(pipeline_file_path, str) or not pipeline_file_path.strip():
    raise errors.PipelineLoadError(
        f"Every `pipelines` entry of {location_description} must set"
        " `source`."
    )
  if _OPEN_TAG_MASK in pipeline_file_path:
    raise errors.PipelineLoadError(
        f"`pipelines[].source` of {location_description} cannot contain"
        " template variables (`{{{{ }}}}`)."
    )
  return pipeline_file_path


def _GetDefaultPipelineFilePath() -> pathlib.Path:
  """Returns `./pipeline.yaml` in the working directory."""
  return pathlib.Path.cwd() / DEFAULT_PIPELINE_FILE_NAME


def _SelectPipelineFilePath(
    args: argparse.Namespace,
    deployment_file_path: pathlib.Path | None,
    pipeline_file_paths: Sequence[pathlib.Path],
) -> pathlib.Path:
  """Selects the single pipeline path to deploy, honoring `--pipeline`."""
  pipeline_arg = args.pipeline
  if deployment_file_path is None:
    if pipeline_arg:
      return pathlib.Path.cwd() / pipeline_arg
    return _GetDefaultPipelineFilePath()
  if pipeline_arg:
    selected_pipeline_file_path = _NormalizePath(
        deployment_file_path.parent / pipeline_arg
    )
    listed_pipeline_file_paths = {
        _NormalizePath(pipeline_file_path)
        for pipeline_file_path in pipeline_file_paths
    }
    if selected_pipeline_file_path not in listed_pipeline_file_paths:
      raise errors.PipelineLoadError(
          f"Pipeline '{pipeline_arg}' not found in"
          f" '{deployment_file_path}'."
      )
    return selected_pipeline_file_path
  if not pipeline_file_paths:
    return _GetDefaultPipelineFilePath()
  if len(pipeline_file_paths) > 1:
    raise errors.AmbiguousPipelineError(
        f"Environment '{args.environment}' in '{deployment_file_path}' lists"
        f" {len(pipeline_file_paths)} pipelines; pass `--pipeline=<source>` to"
        " deploy one of them."
    )
  return pipeline_file_paths[0]


def _NormalizePath(path: pathlib.Path) -> pathlib.Path:
  """Collapses `.` and `..` segments so equivalent spellings compare equal."""
  # Lexical only: symlinks are kept so paths stay as written in the YAML.
  return pathlib.Path(os.path.normpath(path))


def _VerifyNoTemplateTags(resolved_pipeline: ResolvedPipeline) -> None:
  """Verifies the pipeline YAML holds no unexpanded `{{ }}` template tags."""
  if _ContainsMaskedTemplateTag(resolved_pipeline.raw_pipeline_yaml):
    raise errors.PipelineLoadError(
        "Template variables (`{{ }}`) are not supported in Serverless"
        " Orchestration pipeline YAML yet; use literal values in"
        f" '{resolved_pipeline.pipeline_file_path}'."
    )


def _ContainsMaskedTemplateTag(value: Any) -> bool:
  """Returns True if any key or string in `value` holds a masked `{{ }}` tag."""
  if isinstance(value, str):
    return _OPEN_TAG_MASK in value
  if isinstance(value, Mapping):
    return any(
        _ContainsMaskedTemplateTag(k) or _ContainsMaskedTemplateTag(v)
        for k, v in value.items()
    )
  if isinstance(value, list):
    return any(_ContainsMaskedTemplateTag(item) for item in value)
  return False


def _GetTypedFieldFromMapping(
    mapping: Mapping[str, Any],
    key: str,
    expected_type: type[Any],
    source_description: str,
    default: Any = None,
) -> Any:
  """Returns `mapping.get(key, default)` checked against `expected_type`."""
  value = mapping.get(key)
  if value is None:
    return default
  if not isinstance(value, expected_type):
    raise errors.PipelineLoadError(
        f"{source_description}: `{key}` must be a {expected_type.__name__}."
    )
  return value


def _GetNonEmptyStringFromMapping(
    mapping: Mapping[str, Any],
    key: str,
    source_description: str,
    default: str | None = None,
) -> str:
  """Returns the non-empty string at `key`, or `default` when it is absent."""
  value = _GetTypedFieldFromMapping(
      mapping, key, str, source_description, default=default
  )
  if not value or not value.strip():
    raise errors.PipelineLoadError(
        f"{source_description} must specify `{key}`."
    )
  return value


def _GetOptionalNonEmptyStringFromMapping(
    mapping: Mapping[str, Any],
    key: str,
    source_description: str,
) -> str | None:
  """Returns the non-empty string at `key`, or None when `key` is absent."""
  if mapping.get(key) is None:
    return None
  return _GetNonEmptyStringFromMapping(mapping, key, source_description)


def _GetDbtActionFromPipelineYaml(
    raw_actions: Any, base_directory: pathlib.Path
) -> DbtAction:
  """Parses and validates the single dbt action from `raw_actions`."""
  action_entry = _GetSingleActionFromPipelineYaml(raw_actions)
  name = _GetNonEmptyStringFromMapping(action_entry, "name", "The dbt action")
  source_description = f"Action '{name}'"
  dbt_config = _GetDbtConfigFromActionEntry(action_entry, source_description)
  return DbtAction(
      name=name,
      project_directory=_GetDbtProjectDirectory(
          dbt_config, base_directory, source_description
      ),
      # Must be quoted in YAML: `dbtVersion: 1.10` would parse as the float 1.1.
      dbt_version=_GetNonEmptyStringFromMapping(
          dbt_config, "dbtVersion", source_description
      ),
      command=_GetNonEmptyStringFromMapping(
          dbt_config, "command", source_description, default="build"
      ),
      select=_GetSelectModelsFromDbtConfig(dbt_config, source_description),
      variables=dict(
          _GetTypedFieldFromMapping(
              dbt_config, "vars", Mapping, source_description, default={}
          )
      ),
      profile_config=dict(
          _GetTypedFieldFromMapping(
              dbt_config,
              "profileConfig",
              Mapping,
              source_description,
              default={},
          )
      ),
      full_refresh=_GetTypedFieldFromMapping(
          dbt_config, "fullRefresh", bool, source_description, default=False
      ),
  )


def _GetSingleActionFromPipelineYaml(raw_actions: Any) -> Mapping[str, Any]:
  """Returns the single action mapping from `raw_actions`."""
  if (
      not isinstance(raw_actions, list)
      or len(raw_actions) != 1
      or not isinstance(raw_actions[0], Mapping)
  ):
    raise errors.PipelineLoadError(
        "Pipeline YAML must define `actions` with exactly one dbt action."
    )
  return raw_actions[0]


def _GetDbtConfigFromActionEntry(
    action_entry: Mapping[str, Any], source_description: str
) -> Mapping[str, Any]:
  """Returns the validated `framework.dbt` mapping from `action_entry`."""
  framework = _GetTypedFieldFromMapping(
      action_entry, "framework", Mapping, source_description, default={}
  )
  dbt_config = _GetTypedFieldFromMapping(
      framework, "dbt", Mapping, source_description
  )
  if dbt_config is None:
    raise errors.PipelineLoadError(
        f"{source_description} must define `framework.dbt`."
    )
  return dbt_config


def _GetDbtProjectDirectory(
    dbt_config: Mapping[str, Any],
    base_directory: pathlib.Path,
    source_description: str,
) -> pathlib.Path:
  """Returns the validated dbt project directory resolved against base_directory."""
  project_directory = base_directory / _GetNonEmptyStringFromMapping(
      dbt_config, "projectDirectoryPath", source_description
  )
  if not project_directory.is_dir():
    raise errors.PipelineLoadError(
        f"{source_description}: dbt project directory '{project_directory}'"
        " does not exist."
    )
  return project_directory


def _GetSelectModelsFromDbtConfig(
    dbt_config: Mapping[str, Any], source_description: str
) -> tuple[str, ...]:
  """Returns the validated `select` model selectors from `dbt_config`."""
  select = _GetTypedFieldFromMapping(
      dbt_config, "select", list, source_description, default=[]
  )
  if not all(isinstance(item, str) and item.strip() for item in select):
    raise errors.PipelineLoadError(
        f"{source_description}: `select` must list strings."
    )
  return tuple(select)


def _GetEnvironmentModelFromDeploymentFile(
    args: argparse.Namespace,
    deployment_file_path: pathlib.Path | None,
) -> deployment_model.EnvironmentModel | None:
  """Parses `--environment` from `deployment.yaml` via `yaml_processor`."""
  if deployment_file_path is None:
    return None
  environment_name = args.environment
  try:
    external_vars = yaml_processor.collect_external_vars(
        args=args,
        bundle_path=deployment_file_path.parent,
        enforce_clean=False,
        bundle_name=None,
    )
    _, _, environment = yaml_processor.parse_deployment(
        str(deployment_file_path), environment_name, external_vars
    )
  # yaml_processor leaks these for malformed `variables` and `resources`.
  except (
      exceptions.Error,
      yaml.Error,
      AttributeError,
      KeyError,
      TypeError,
      ValueError,
  ) as e:
    raise errors.PipelineLoadError(
        f"Failed to load environment '{environment_name}' from"
        f" '{deployment_file_path}': {e}"
    ) from e
  _VerifyServerlessEnvironment(
      environment, environment_name, deployment_file_path
  )
  return environment


def _VerifyServerlessEnvironment(
    environment: deployment_model.EnvironmentModel,
    environment_name: str,
    deployment_file_path: pathlib.Path,
) -> None:
  """Verifies `environment` does not set Cloud Composer-only fields."""
  if environment.composer_environment is not None:
    raise errors.PipelineLoadError(
        f"Environment '{environment_name}' in '{deployment_file_path}'"
        " specifies `composer_environment`, which is not supported for"
        f" `runner: {ORCHESTRATION_SERVICE_RUNNER}`."
    )


def _GetProjectId(
    environment: deployment_model.EnvironmentModel | None,
    defaults: Mapping[str, Any],
    source_description: str,
) -> str:
  """Returns project from `deployment.yaml`, `defaults.projectId`, or gcloud."""
  environment_project = environment.project if environment else None
  default_project = _GetOptionalNonEmptyStringFromMapping(
      defaults, "projectId", source_description
  )
  _LogIgnoredPipelineDefault("projectId", default_project, environment_project)
  project = (
      environment_project
      or default_project
      or properties.VALUES.core.project.Get()
  )
  if not project or not project.strip():
    raise errors.PipelineLoadError(
        "Project must be set via `deployment.yaml` (`project`),"
        " `defaults.projectId` or `--project`."
    )
  return project


def _GetLocation(
    environment: deployment_model.EnvironmentModel | None,
    defaults: Mapping[str, Any],
    source_description: str,
) -> str:
  """Returns location from `deployment.yaml` `region` or `defaults.location`."""
  environment_location = environment.region if environment else None
  default_location = _GetOptionalNonEmptyStringFromMapping(
      defaults, "location", source_description
  )
  _LogIgnoredPipelineDefault("location", default_location, environment_location)
  location = environment_location or default_location
  if not location or not location.strip():
    raise errors.PipelineLoadError(
        "Location must be set via `deployment.yaml` (`region`) or"
        " `defaults.location`."
    )
  return location


def _LogIgnoredPipelineDefault(
    default_key: str,
    default_value: str | None,
    environment_value: str | None,
) -> None:
  """Logs when `deployment.yaml` overrides a different `pipeline.yaml` default."""
  if default_value and environment_value and default_value != environment_value:
    log.info(
        "Using '%s' from `deployment.yaml`; `defaults.%s: %s` in"
        " `pipeline.yaml` is ignored.",
        environment_value,
        default_key,
        default_value,
    )


def _GetServiceAccountEmail(
    environment: deployment_model.EnvironmentModel | None,
    defaults: Mapping[str, Any],
    source_description: str,
) -> str | None:
  """Returns the pipeline execution service account email, when configured."""
  environment_service_account = (
      environment.service_account if environment else None
  )
  default_service_account = _GetOptionalNonEmptyStringFromMapping(
      defaults, "serviceAccount", source_description
  )
  _LogIgnoredPipelineDefault(
      "serviceAccount", default_service_account, environment_service_account
  )
  return environment_service_account or default_service_account


def _GetArtifactBucketAndPathPrefix(
    environment: deployment_model.EnvironmentModel | None,
    project: str,
    location: str,
) -> tuple[str, str]:
  """Returns `(artifact_bucket, artifact_path_prefix)` for the deployment."""
  artifact_storage = environment.artifact_storage if environment else None
  if artifact_storage:
    return artifact_storage.bucket, artifact_storage.path_prefix or ""
  project_number = _GetProjectNumber(project)
  return f"dcs-artifacts-{project_number}-{location}", ""


def _GetProjectNumber(project: str) -> str:
  """Returns the numeric project number for `project`."""
  if project.isdigit():
    return project
  try:
    project_number = projects_util.GetProjectNumber(project)
  except Exception as e:
    raise errors.PipelineLoadError(
        f"Failed to resolve project number for project '{project}': {e}"
    ) from e
  if not project_number:
    raise errors.PipelineLoadError(
        f"Failed to resolve project number for project '{project}'."
    )
  return str(project_number)
