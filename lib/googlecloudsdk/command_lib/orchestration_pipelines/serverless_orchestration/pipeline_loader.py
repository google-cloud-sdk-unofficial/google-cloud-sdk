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
"""Loads a Serverless Orchestration pipeline YAML and its environment settings.

A pipeline declares its data models under `spec.dataPipeline.dataModels`,
mirroring the Orchestration API's `Pipeline.spec` ->
`PipelineSpec.data_pipeline` -> `DataPipeline.data_models`. Each entry is a
`DataModel`: an `id` and exactly one of:

- `sdp`: a Spark Declarative Pipelines project (`SdpModelSpec`).
- `dbt`: a dbt project (`DbtModelSpec`).

The pipeline's execution identity comes from `deployment.yaml`
(`service_account`) or the pipeline's `executionIdentity.serviceAccount.email`
(`Pipeline.execution_identity`).
"""

import argparse
from collections.abc import Mapping, Sequence
import dataclasses
import functools
import os
import pathlib
import re
from typing import Any, TypeAlias

from googlecloudsdk.api_lib.storage import storage_util
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
SDP_MODEL_TYPE = "sdp"
DBT_MODEL_TYPE = "dbt"

_SPEC_KEY = "spec"
_DATA_PIPELINE_KEY = "dataPipeline"
_DATA_MODELS_KEY = "dataModels"
_DATA_MODELS_PATH = f"{_SPEC_KEY}.{_DATA_PIPELINE_KEY}.{_DATA_MODELS_KEY}"
_EXECUTION_IDENTITY_KEY = "executionIdentity"
_SERVICE_ACCOUNT_EMAIL_PATH = f"{_EXECUTION_IDENTITY_KEY}.serviceAccount.email"
_OPEN_TAG_MASK = "__OPEN_TAG__"
_CLOSE_TAG_MASK = "__CLOSE_TAG__"
# `re.DOTALL` lets a tag span lines, e.g. an escaped `\n` in a quoted scalar.
_TEMPLATE_TAG_RE = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
_MASKED_TAG_RE = re.compile(
    rf"{re.escape(_OPEN_TAG_MASK)}(.*?){re.escape(_CLOSE_TAG_MASK)}",
    re.DOTALL,
)
# Names of template variables. Matched with `fullmatch`.
_IDENTIFIER_RE = re.compile(r"[A-Za-z0-9_]+")
# Variables that `yaml_processor.collect_external_vars` always adds for Cloud
# Composer bundles: a lazily computed Git commit SHA and the bundle directory
# name. They are not template variables of `pipeline.yaml`.
_COMPOSER_BUNDLE_VARIABLES = ("COMMIT_SHA", "BUNDLE_ID")
_SUBSTITUTION_VARIABLE_LABEL = "Substitution variable"
_DEPLOYMENT_VARIABLE_LABEL = "`deployment.yaml` variable"
# YAML scalars, which template variables and string mappings can hold.
_SCALAR_TYPES = (str, int, float, bool)
_ScalarValue: TypeAlias = str | int | float | bool
# Data model IDs become artifact path segments (staging directories and Cloud
# Storage prefixes), so they must start with an alphanumeric character; this
# also rules out `.` and `..`. Matched with `fullmatch`.
_MODEL_ID_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}")
_MODEL_ID_RULE = (
    "must be 1-64 characters of letters, digits, `_`, `.`, or `-`, and start"
    " with a letter or digit"
)
_SDP_SPEC_CANDIDATES = ("spark-pipeline.yml", "spark-pipeline.yaml")
# Keys supported under `spec` (`PipelineSpec`: only `data_pipeline`),
# `spec.dataPipeline` (`DataPipeline`), a `dataModels` entry (`DataModel`: `id`
# plus the `model_type` oneof), its `sdp` (`SdpDataModel` fields the CLI reads
# from `pipeline.yaml`) and `sdp.executionConfig` (`SdpExecutionConfig`); any
# other key is rejected rather than silently ignored.
_SUPPORTED_SPEC_KEYS = (_DATA_PIPELINE_KEY,)
_SUPPORTED_DATA_PIPELINE_KEYS = (_DATA_MODELS_KEY,)
_SUPPORTED_DATA_MODEL_KEYS = ("id", SDP_MODEL_TYPE, DBT_MODEL_TYPE)
_SUPPORTED_SDP_KEYS = ("specPath", "executionConfig")
_SUPPORTED_EXECUTION_CONFIG_KEYS = ("jarUris", "subnetwork", "properties")
# `ExecutionIdentity` (the `end_user` arm of its oneof is output-only) and
# `ServiceAccountIdentity`.
_SUPPORTED_EXECUTION_IDENTITY_KEYS = ("serviceAccount",)
_SUPPORTED_SERVICE_ACCOUNT_IDENTITY_KEYS = ("email",)
# Matches the Orchestration API's `SdpExecutionConfig.subnetwork` format.
# Matched with `fullmatch`.
_SUBNETWORK_NAME_RE = re.compile(
    r"projects/[^/\s]+/regions/[^/\s]+/subnetworks/[^/\s]+"
)

# A `gs://<bucket>[/<path>]` URI without whitespace or empty path segments;
# `storage_util` checks the bucket name. Matched with `fullmatch`.
_GCS_URI_RE = re.compile(r"gs://(?P<bucket>[^/\s]+)(?:/[^/\s]+)*")
# Keys supported at the top level of `pipeline.yaml`, in `defaults`, in
# `outputArtifactStorage` and its `gcs`, and in a data model's `dbt` and its
# `dbt.managedRuntime`; any other key is rejected rather than silently ignored.
# For example, dbt `command`, `select` and `vars` are not supported: the
# Orchestration service always runs `dbt build` on the whole dbt project.
_SUPPORTED_PIPELINE_KEYS = (
    "pipelineId",
    "runner",
    "description",
    "defaults",
    _EXECUTION_IDENTITY_KEY,
    "outputArtifactStorage",
    _SPEC_KEY,
)
_SUPPORTED_DEFAULTS_KEYS = ("projectId", "location")
_SUPPORTED_OUTPUT_ARTIFACT_STORAGE_KEYS = ("gcs",)
_SUPPORTED_GCS_STORAGE_KEYS = ("uri",)
_SUPPORTED_DBT_KEYS = ("sourcePath", "managedRuntime", "profileConfig")
_SUPPORTED_MANAGED_RUNTIME_KEYS = ("dbtVersion",)


@dataclasses.dataclass(frozen=True)
class DbtModelSpec:
  """Configuration of a dbt data model (`DataModel.dbt` in the API).

  Attributes:
    id: ID of the data model, unique within the pipeline (`DataModel.id`).
    project_directory: Absolute path of the dbt project directory.
    dbt_version: Version of the Google-managed dbt runtime, e.g. `1.9`.
    profile_config: Literal `profileConfig` values, rendered into
      `profiles.yml` when packaging; empty when `profileConfig` is not set.
  """

  id: str
  project_directory: pathlib.Path
  dbt_version: str
  profile_config: Mapping[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class SdpExecutionConfig:
  """Settings for running an SDP data model (`SdpExecutionConfig` in the API).

  Attributes:
    jar_uris: `gs://` URIs of JARs added to the driver and executor classpath.
    subnetwork: Full resource name of the subnetwork the batch runs in, or None
      to use the default network.
    properties: Spark properties (`spark.*`) for the batch workload. YAML
      scalars are converted to strings; version-like values must be quoted in
      `pipeline.yaml` (`"1.10"`), since `1.10` parses as the float `1.1`.
  """

  jar_uris: tuple[str, ...] = ()
  subnetwork: str | None = None
  properties: Mapping[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class SdpModelSpec:
  """Configuration of an SDP data model (`DataModel.sdp` in the API).

  Attributes:
    id: ID of the data model, unique within the pipeline (`DataModel.id`).
    project_directory: Directory containing `spec_path`, against which the
      `spark-pipeline.yml` libraries are resolved.
    spec_path: Resolved local path of the `spark-pipeline.yml`.
    execution_config: Serverless Spark execution settings.
  """

  id: str
  project_directory: pathlib.Path
  spec_path: pathlib.Path
  execution_config: SdpExecutionConfig = dataclasses.field(
      default_factory=SdpExecutionConfig
  )


@dataclasses.dataclass(frozen=True)
class LoadedPipeline:
  """Validated pipeline configuration and target environment settings.

  Attributes:
    pipeline_id: The `pipelineId` of the pipeline YAML.
    project: Project to deploy to: `deployment.yaml` `project`,
      `defaults.projectId`, or the `core/project` property.
    location: Region to deploy to: `deployment.yaml` `region` or
      `defaults.location`.
    target: The deployment environment (`--environment`), or `default`; also
      the dbt target name.
    service_account: Email of the service account the pipeline runs as.
    artifact_bucket: Bucket name without `gs://`, from `deployment.yaml`
      `artifact_storage` or the `dcs-artifacts-<projectNumber>-<location>`
      default.
    base_dir: Directory containing the pipeline YAML.
    dbt_models: Validated `dbt` entries of `spec.dataPipeline.dataModels`.
    artifact_path_prefix: `artifact_storage.path_prefix` of `deployment.yaml`;
      empty when not set.
    sdp_models: Validated `sdp` entries of `spec.dataPipeline.dataModels`.
    output_artifact_storage_uri: Normalized `outputArtifactStorage.gcs.uri` of
      the pipeline YAML, or None when `outputArtifactStorage` is not set; runs
      then write their outputs to `pipelines/<pipeline_id>/outputs` under
      `artifact_bucket` and `artifact_path_prefix`.
  """

  pipeline_id: str
  project: str
  location: str
  target: str
  service_account: str
  artifact_bucket: str
  base_dir: pathlib.Path
  dbt_models: tuple[DbtModelSpec, ...] = ()
  artifact_path_prefix: str = ""
  sdp_models: tuple[SdpModelSpec, ...] = ()
  output_artifact_storage_uri: str | None = None


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
  raw_pipeline_yaml, environment = _ResolvePipelineYaml(resolved_pipeline, args)
  pipeline_file_path = resolved_pipeline.pipeline_file_path
  source_description = f"Pipeline '{pipeline_file_path}'"
  environment_name = args.environment
  _VerifyTopLevelPipelineFields(raw_pipeline_yaml, source_description)
  pipeline_id = _GetNonEmptyStringFromMapping(
      raw_pipeline_yaml, "pipelineId", source_description
  )
  defaults = _GetDefaultsFromPipelineYaml(raw_pipeline_yaml, source_description)
  output_artifact_storage_uri = _GetOutputArtifactStorageUri(
      raw_pipeline_yaml, source_description
  )
  project = _GetProjectId(environment, defaults, source_description)
  location = _GetLocation(environment, defaults, source_description)
  dbt_models, sdp_models = _GetDataModelsFromPipelineYaml(
      raw_pipeline_yaml, pipeline_file_path.parent, project, location
  )
  service_account = _GetServiceAccountEmail(
      environment, raw_pipeline_yaml, source_description
  )
  artifact_bucket, artifact_path_prefix = _GetArtifactBucketAndPathPrefix(
      environment, project, location
  )
  return LoadedPipeline(
      pipeline_id=pipeline_id,
      project=project,
      location=location,
      target=environment_name or "default",
      service_account=service_account,
      artifact_bucket=artifact_bucket,
      base_dir=pipeline_file_path.parent,
      dbt_models=dbt_models,
      artifact_path_prefix=artifact_path_prefix,
      sdp_models=sdp_models,
      output_artifact_storage_uri=output_artifact_storage_uri,
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


def _ResolvePipelineYaml(
    resolved_pipeline: ResolvedPipeline, args: argparse.Namespace
) -> tuple[Mapping[str, Any], deployment_model.EnvironmentModel | None]:
  """Loads the target environment and resolves the pipeline's template tags.

  Args:
    resolved_pipeline: The selected pipeline YAML and `deployment.yaml` path.
    args: The parsed command-line arguments. `--environment` selects the
      `deployment.yaml` environment; `--substitutions`, `--substitutions-file`
      and `_DEPLOY_VAR_*` environment variables set substitution variables.

  Returns:
    `(raw_pipeline_yaml, environment)`: the pipeline YAML with its `{{ }}` tags
    resolved, and the `deployment.yaml` environment, or None without
    `deployment.yaml`.

  Raises:
    errors.PipelineLoadError: If a top-level key, `pipelineId` or `runner` is
      templated, a substitution variable or the environment is invalid, or a
      tag cannot be resolved.
  """
  source_description = f"Pipeline '{resolved_pipeline.pipeline_file_path}'"
  _VerifyLiteralTopLevelFields(
      resolved_pipeline.raw_pipeline_yaml, source_description
  )
  external_variables = _CollectExternalVariables(args)
  substitution_variables = _GetSubstitutionVariables(external_variables)
  environment = _GetEnvironmentModelFromDeploymentFile(
      args.environment,
      resolved_pipeline.deployment_file_path,
      external_variables,
  )
  template_variables = _BuildTemplateVariablesMap(
      args.environment, environment, substitution_variables
  )
  raw_pipeline_yaml = _ResolveMaskedTemplateTags(
      resolved_pipeline.raw_pipeline_yaml,
      template_variables,
      source_description,
  )
  return raw_pipeline_yaml, environment


def _VerifyLiteralTopLevelFields(
    raw_pipeline_yaml: Mapping[str, Any], source_description: str
) -> None:
  """Verifies that the top-level keys, `pipelineId` and `runner` are literals.

  `pipelineId` names the deployed pipeline, and `deploy` reads `runner` before
  template resolution to pick the deployment flow. A templated top-level key
  could resolve to either of them.

  Args:
    raw_pipeline_yaml: The pipeline YAML mapping, before template resolution.
    source_description: Describes the pipeline YAML for error messages.

  Raises:
    errors.PipelineLoadError: If a top-level key, `pipelineId` or `runner`
      contains a `{{ }}` tag.
  """
  for key in raw_pipeline_yaml:
    if _ContainsMaskedTemplateTag(key):
      raise errors.PipelineLoadError(
          f"{source_description}: top-level key"
          f" '{_UnmaskTemplateTags(str(key))}' cannot contain template"
          " variables (`{{ }}`)."
      )
  for field_name in ("pipelineId", "runner"):
    if _ContainsMaskedTemplateTag(raw_pipeline_yaml.get(field_name)):
      raise errors.PipelineLoadError(
          f"{source_description}: `{field_name}` cannot contain template"
          " variables (`{{ }}`)."
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


def _UnmaskTemplateTags(value: str) -> str:
  """Restores the `{{` and `}}` that `LoadRawYamlMapping` masked in `value`."""
  return value.replace(_OPEN_TAG_MASK, "{{").replace(_CLOSE_TAG_MASK, "}}")


def _CollectExternalVariables(args: argparse.Namespace) -> dict[str, Any]:
  """Collects the external variables of the deployment.

  These are `_DEPLOY_VAR_*` environment variables, `--substitutions-file` and
  `--substitutions`, in increasing precedence, plus the Cloud Composer bundle
  variables (`_COMPOSER_BUNDLE_VARIABLES`) that `yaml_processor` always adds.

  Args:
    args: The parsed command-line arguments.

  Returns:
    The external variables keyed by name, with values as parsed.

  Raises:
    errors.PipelineLoadError: If the substitutions file cannot be loaded.
  """
  try:
    return yaml_processor.collect_external_vars(
        args=args,
        # Only the Cloud Composer bundle variables, which are not template
        # variables of `pipeline.yaml`, depend on the bundle path.
        bundle_path=pathlib.Path.cwd(),
        enforce_clean=False,
        bundle_name=None,
    )
  except (exceptions.Error, yaml.Error, UnicodeDecodeError) as e:
    raise errors.PipelineLoadError(
        f"Failed to load substitution variables: {e}"
    ) from e


def _GetSubstitutionVariables(
    external_variables: Mapping[str, Any],
) -> dict[str, _ScalarValue]:
  """Returns the user's substitution variables from `external_variables`.

  Args:
    external_variables: The variables from `_CollectExternalVariables`.

  Returns:
    `external_variables` without the Cloud Composer bundle variables.

  Raises:
    errors.PipelineLoadError: If a substitution variable name is not a
      non-empty string, or a value is not a scalar.
  """
  return _GetScalarVariables(
      {
          key: value
          for key, value in external_variables.items()
          if key not in _COMPOSER_BUNDLE_VARIABLES
      },
      _SUBSTITUTION_VARIABLE_LABEL,
  )


def _GetScalarVariables(
    variables: Mapping[Any, Any], source_label: str
) -> dict[str, _ScalarValue]:
  """Returns `variables`, verifying that keys are strings and values scalars.

  Args:
    variables: The variables of one source, keyed by name.
    source_label: Names the source of `variables` in error messages.

  Returns:
    The variables, keyed by name.

  Raises:
    errors.PipelineLoadError: If a key is not a non-empty string (YAML parses
      unquoted keys such as `on`, `yes` or `123` as other types), or a value
      is not a str, int, float or bool.
  """
  scalar_variables: dict[str, _ScalarValue] = {}
  for key, value in variables.items():
    if not isinstance(key, str) or not key.strip():
      raise errors.PipelineLoadError(
          f"{source_label} name '{key}' must be a non-empty string; quote"
          " names that YAML parses as other types, such as `on` or `123`."
      )
    if not isinstance(value, _SCALAR_TYPES):
      raise errors.PipelineLoadError(
          f"{source_label} '{key}' must be a scalar value (str, int, float, or"
          " bool)."
      )
    scalar_variables[key] = value
  return scalar_variables


def _BuildTemplateVariablesMap(
    environment_name: str | None,
    environment: deployment_model.EnvironmentModel | None,
    substitution_variables: Mapping[str, _ScalarValue],
) -> dict[str, _ScalarValue]:
  """Builds the variables that resolve the template tags of `pipeline.yaml`.

  Substitution variables override `deployment.yaml` `variables`. Neither can
  set a built-in variable (`env`, `project`, `region`, `service_account`) to a
  different value; setting the same value is allowed, and the built-in keeps
  its string value.

  Args:
    environment_name: The target environment (`--environment`), or None.
    environment: The `deployment.yaml` environment, or None without one.
    substitution_variables: The validated substitution variables.

  Returns:
    The template variables keyed by name.

  Raises:
    errors.PipelineLoadError: If a `deployment.yaml` variable name is not a
      non-empty string or its value is not a scalar, or a variable sets a
      built-in variable to a different value.
  """
  builtin_variables = _GetBuiltinTemplateVariables(
      environment_name, environment
  )
  deployment_variables = _GetDeploymentVariables(environment)
  # `yaml_processor` resolves `deployment.yaml` with substitutions overriding
  # its `variables`, so only the effective variables can conflict.
  _VerifyNoBuiltinVariableConflict(
      builtin_variables,
      {
          key: value
          for key, value in deployment_variables.items()
          if key not in substitution_variables
      },
      _DEPLOYMENT_VARIABLE_LABEL,
  )
  _VerifyNoBuiltinVariableConflict(
      builtin_variables, substitution_variables, _SUBSTITUTION_VARIABLE_LABEL
  )
  return {**deployment_variables, **substitution_variables, **builtin_variables}


def _GetBuiltinTemplateVariables(
    environment_name: str | None,
    environment: deployment_model.EnvironmentModel | None,
) -> dict[str, str]:
  """Returns the built-in template variables of the target environment.

  `env` is the target environment name. `project`, `region` and
  `service_account` come from the `deployment.yaml` environment, which
  `yaml_processor` validated as non-empty strings.

  Args:
    environment_name: The target environment (`--environment`), or None.
    environment: The `deployment.yaml` environment, or None without one.

  Returns:
    The built-in variables that are set, keyed by name.
  """
  builtin_variables: dict[str, str] = {}
  if environment_name:
    builtin_variables["env"] = environment_name
  if environment is not None:
    builtin_variables["project"] = environment.project
    builtin_variables["region"] = environment.region
    if environment.service_account is not None:
      builtin_variables["service_account"] = environment.service_account
  return builtin_variables


def _GetDeploymentVariables(
    environment: deployment_model.EnvironmentModel | None,
) -> dict[str, _ScalarValue]:
  """Returns the validated `variables` of the `deployment.yaml` environment.

  Args:
    environment: The `deployment.yaml` environment, or None without one.

  Returns:
    The variables keyed by name; empty without `deployment.yaml` or
    `variables`.

  Raises:
    errors.PipelineLoadError: If a variable name is not a non-empty string, or
      a value is not a scalar.
  """
  if environment is None or not environment.variables:
    return {}
  return _GetScalarVariables(environment.variables, _DEPLOYMENT_VARIABLE_LABEL)


def _VerifyNoBuiltinVariableConflict(
    builtin_variables: Mapping[str, str],
    candidate_variables: Mapping[str, _ScalarValue],
    source_label: str,
) -> None:
  """Verifies that no variable sets a built-in variable to a different value.

  Args:
    builtin_variables: The built-in template variables.
    candidate_variables: The variables of another source.
    source_label: Names the source of `candidate_variables` in error messages.

  Raises:
    errors.PipelineLoadError: If a variable sets a built-in variable to a
      different value.
  """
  for key, value in candidate_variables.items():
    builtin_value = builtin_variables.get(key)
    if builtin_value is None:
      continue
    str_value = _ScalarToString(value)
    if str_value != builtin_value:
      raise errors.PipelineLoadError(
          f"{source_label} '{key}' ('{str_value}') conflicts with target"
          f" environment value '{builtin_value}'."
      )


def _ScalarToString(value: _ScalarValue) -> str:
  """Converts a YAML scalar to a string, formatting booleans in lowercase."""
  if isinstance(value, bool):
    return str(value).lower()
  return str(value)


def _ResolveMaskedTemplateTags(
    value: Any,
    template_variables: Mapping[str, _ScalarValue],
    source_description: str,
) -> Any:
  """Returns `value` with its masked `{{ KEY }}` tags resolved, recursively.

  Args:
    value: A parsed YAML value: a mapping, list, string or other scalar.
    template_variables: The variables that resolve the tags.
    source_description: Describes the YAML file for error messages.

  Returns:
    A copy of `value` whose strings and mapping keys have their tags resolved;
    other scalars are returned unchanged.

  Raises:
    errors.PipelineLoadError: If a tag cannot be resolved, or two keys of a
      mapping resolve to the same key.
  """
  if isinstance(value, str):
    return _ResolveMaskedTemplateString(
        value, template_variables, source_description
    )
  if isinstance(value, Mapping):
    return _ResolveMaskedTemplateMapping(
        value, template_variables, source_description
    )
  if isinstance(value, list):
    return [
        _ResolveMaskedTemplateTags(item, template_variables, source_description)
        for item in value
    ]
  return value


def _ResolveMaskedTemplateMapping(
    mapping: Mapping[Any, Any],
    template_variables: Mapping[str, _ScalarValue],
    source_description: str,
) -> dict[Any, Any]:
  """Returns `mapping` with the tags in its keys and values resolved.

  Args:
    mapping: A parsed YAML mapping.
    template_variables: The variables that resolve the tags.
    source_description: Describes the YAML file for error messages.

  Returns:
    The resolved mapping. String keys stay strings, even when a key is a single
    tag whose variable is a number or boolean.

  Raises:
    errors.PipelineLoadError: If a tag cannot be resolved, or two keys resolve
      to the same key.
  """
  resolved_mapping: dict[Any, Any] = {}
  for key, item_value in mapping.items():
    resolved_key = key
    if isinstance(key, str):
      resolved_key = _ScalarToString(
          _ResolveMaskedTemplateString(
              key, template_variables, source_description
          )
      )
    if resolved_key in resolved_mapping:
      raise errors.PipelineLoadError(
          f"Duplicate mapping key '{resolved_key}' after template variable"
          f" resolution in {source_description}."
      )
    resolved_mapping[resolved_key] = _ResolveMaskedTemplateTags(
        item_value, template_variables, source_description
    )
  return resolved_mapping


def _ResolveMaskedTemplateString(
    value: str,
    template_variables: Mapping[str, _ScalarValue],
    source_description: str,
) -> _ScalarValue:
  """Returns `value` with its masked `{{ KEY }}` tags resolved.

  A value that is exactly one tag resolves to the variable's value and type,
  so `threads: {{ count }}` stays an int. Tags embedded in a longer string are
  replaced by the string form of their values, with booleans in lowercase as
  in YAML (`true`).

  Args:
    value: A string of the parsed YAML, with masked tags.
    template_variables: The variables that resolve the tags.
    source_description: Describes the YAML file for error messages.

  Returns:
    The resolved value.

  Raises:
    errors.PipelineLoadError: If `value` has an unmatched `{{` or `}}`, or a
      tag names an invalid or undefined variable.
  """
  _VerifyNoUnmatchedTemplateDelimiter(value, source_description)
  first_tag = _MASKED_TAG_RE.match(value)
  if first_tag is not None and first_tag.end() == len(value):
    return _LookupTemplateVariable(
        first_tag.group(1), template_variables, source_description
    )
  replacer = functools.partial(
      _ReplaceTemplateTagMatch, template_variables, source_description
  )
  return _MASKED_TAG_RE.sub(replacer, value)


def _VerifyNoUnmatchedTemplateDelimiter(
    value: str, source_description: str
) -> None:
  """Verifies that `value` has no `{{` or `}}` outside of a complete tag.

  `LoadRawYamlMapping` masks every `{{ ... }}` of the raw text, so a literal
  `{{` or `}}` left in `value` is unmatched, even inside a masked tag (e.g.
  `{{ a {{ b }}`). A `{{` and a `}}` of different scalars or comments, e.g.
  `a: "{{ x"  # y }}`, leave a lone mask in each parsed string instead.

  Args:
    value: A string of the parsed YAML, with masked tags.
    source_description: Describes the YAML file for error messages.

  Raises:
    errors.PipelineLoadError: If `value` has an unmatched `{{` or `}}`.
  """
  outside_tags = _MASKED_TAG_RE.sub("", value)
  if (
      "{{" in value
      or "}}" in value
      or _OPEN_TAG_MASK in outside_tags
      or _CLOSE_TAG_MASK in outside_tags
  ):
    raise errors.PipelineLoadError(
        f"Unmatched template tag delimiter in {source_description}:"
        f" '{_UnmaskTemplateTags(value)}'."
    )


def _ReplaceTemplateTagMatch(
    template_variables: Mapping[str, _ScalarValue],
    source_description: str,
    match: re.Match[str],
) -> str:
  """Returns the string value of the matched template variable."""
  return _ScalarToString(
      _LookupTemplateVariable(
          match.group(1), template_variables, source_description
      )
  )


def _LookupTemplateVariable(
    raw_name: str,
    template_variables: Mapping[str, _ScalarValue],
    source_description: str,
) -> _ScalarValue:
  """Returns the value of the template variable that a tag names.

  Args:
    raw_name: The text between the `{{` and `}}` of the tag.
    template_variables: The variables that resolve the tags.
    source_description: Describes the YAML file for error messages.

  Returns:
    The value of the variable.

  Raises:
    errors.PipelineLoadError: If the name does not match `_IDENTIFIER_RE`, is a
      Cloud Composer bundle variable, or names an undefined variable.
  """
  var_name = raw_name.strip()
  if not _IDENTIFIER_RE.fullmatch(var_name):
    raise errors.PipelineLoadError(
        f"Invalid template variable '{{{{ {var_name} }}}}' in"
        f" {source_description}; variable names must match"
        f" `{_IDENTIFIER_RE.pattern}`."
    )
  # `yaml_processor` always sets these for Cloud Composer bundles, so their
  # substitution values are dropped; they are rejected whatever their source.
  if var_name in _COMPOSER_BUNDLE_VARIABLES:
    raise errors.PipelineLoadError(
        f"Template variable '{{{{ {var_name} }}}}' in {source_description} is"
        " only set for Cloud Composer deployments; use a variable with another"
        " name."
    )
  try:
    return template_variables[var_name]
  except KeyError:
    raise errors.PipelineLoadError(
        f"Unresolved template variable '{{{{ {var_name} }}}}' in"
        f" {source_description}; define it in `deployment.yaml` `variables`"
        " or `--substitutions`."
    ) from None


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


def _GetRequiredMappingFromMapping(
    mapping: Mapping[str, Any], key: str, source_description: str
) -> Mapping[str, Any]:
  """Returns the mapping at `key`, which must be present and non-null."""
  value = _GetTypedFieldFromMapping(mapping, key, Mapping, source_description)
  if value is None:
    raise errors.PipelineLoadError(f"{source_description} must define `{key}`.")
  return value


def _GetStringDictFromMapping(
    mapping: Mapping[str, Any], key: str, source_description: str
) -> dict[str, str]:
  """Returns a validated `dict[str, str]` from `mapping[key]`.

  Scalar values are converted with `_ScalarToString`, so unquoted YAML numbers
  arrive already parsed: `1.10` becomes `"1.1"`. Values that must keep their
  spelling (versions, zero-padded IDs) have to be quoted in the YAML.

  Args:
    mapping: The YAML mapping holding `key`.
    key: The key of the string-to-scalar mapping; absent means empty.
    source_description: Describes `mapping` for error messages.

  Returns:
    The mapping with its values converted to strings.

  Raises:
    errors.PipelineLoadError: If `mapping[key]` is not a mapping, a key is not
      a non-empty string, or a value is null or not a scalar.
  """
  raw_dict = _GetTypedFieldFromMapping(
      mapping, key, Mapping, source_description, default={}
  )
  result: dict[str, str] = {}
  for dict_key, dict_value in raw_dict.items():
    if not isinstance(dict_key, str) or not dict_key.strip():
      raise errors.PipelineLoadError(
          f"{source_description}: `{key}` keys must be non-empty strings."
      )
    if dict_value is None:
      raise errors.PipelineLoadError(
          f"{source_description}: `{key}.{dict_key}` must not be empty."
      )
    if not isinstance(dict_value, _SCALAR_TYPES):
      raise errors.PipelineLoadError(
          f"{source_description}: `{key}.{dict_key}` must be a scalar value."
      )
    result[dict_key] = _ScalarToString(dict_value)
  return result


def _VerifyTopLevelPipelineFields(
    raw_pipeline_yaml: Mapping[str, Any], source_description: str
) -> None:
  """Verifies the pipeline YAML's top-level keys, `runner` and `description`.

  `deploy` picks this loader from the `runner` of the `deployment.yaml`
  pipelines or of `./pipeline.yaml`, which need not be the file `--pipeline`
  selects. `runner` is therefore checked again here, first, so that a file for
  another runner reports the wrong runner rather than its other keys.
  `description` only documents the pipeline YAML: it is validated, but not
  sent to the Orchestration service.

  Args:
    raw_pipeline_yaml: The pipeline YAML mapping.
    source_description: Describes the pipeline YAML for error messages.

  Raises:
    errors.PipelineLoadError: If the pipeline YAML does not set
      `runner: orchestration_service`, sets an unsupported key, or sets
      `description` to anything but a non-empty string.
  """
  if raw_pipeline_yaml.get("runner") != ORCHESTRATION_SERVICE_RUNNER:
    raise errors.PipelineLoadError(
        f"{source_description} must set"
        f" `runner: {ORCHESTRATION_SERVICE_RUNNER}`."
    )
  _VerifyNoUnsupportedKeys(
      raw_pipeline_yaml, _SUPPORTED_PIPELINE_KEYS, source_description
  )
  _GetOptionalNonEmptyStringFromMapping(
      raw_pipeline_yaml, "description", source_description
  )


def _GetDefaultsFromPipelineYaml(
    raw_pipeline_yaml: Mapping[str, Any], source_description: str
) -> Mapping[str, Any]:
  """Returns the validated `defaults` mapping of the pipeline YAML.

  Args:
    raw_pipeline_yaml: The pipeline YAML mapping.
    source_description: Describes the pipeline YAML for error messages.

  Returns:
    The `defaults` mapping, or an empty mapping when it is absent or null.

  Raises:
    errors.PipelineLoadError: If `defaults` is not a mapping or sets a key
      other than `projectId` and `location`.
  """
  defaults = _GetTypedFieldFromMapping(
      raw_pipeline_yaml, "defaults", Mapping, source_description, default={}
  )
  _VerifyNoUnsupportedKeys(
      defaults, _SUPPORTED_DEFAULTS_KEYS, source_description, "defaults"
  )
  return defaults


def _GetOutputArtifactStorageUri(
    raw_pipeline_yaml: Mapping[str, Any], source_description: str
) -> str | None:
  """Returns the validated `outputArtifactStorage.gcs.uri` of the pipeline.

  Args:
    raw_pipeline_yaml: The pipeline YAML mapping.
    source_description: Describes the pipeline YAML for error messages.

  Returns:
    The URI as normalized by `_NormalizeGcsUri`, or None when
    `outputArtifactStorage` is absent or null, in which case runs write their
    outputs to the default location next to the uploaded artifacts.

  Raises:
    errors.PipelineLoadError: If `outputArtifactStorage` or its `gcs` is not a
      mapping or has unsupported keys, `gcs.uri` is missing, or the URI is
      invalid.
  """
  storage = _GetTypedFieldFromMapping(
      raw_pipeline_yaml, "outputArtifactStorage", Mapping, source_description
  )
  if storage is None:
    return None
  _VerifyNoUnsupportedKeys(
      storage,
      _SUPPORTED_OUTPUT_ARTIFACT_STORAGE_KEYS,
      source_description,
      "outputArtifactStorage",
  )
  gcs_storage = _GetRequiredMappingFromMapping(
      storage, "gcs", f"{source_description} `outputArtifactStorage`"
  )
  _VerifyNoUnsupportedKeys(
      gcs_storage,
      _SUPPORTED_GCS_STORAGE_KEYS,
      source_description,
      "outputArtifactStorage.gcs",
  )
  raw_uri = _GetNonEmptyStringFromMapping(
      gcs_storage, "uri", f"{source_description} `outputArtifactStorage.gcs`"
  )
  return _NormalizeGcsUri(
      raw_uri, f"{source_description} `outputArtifactStorage.gcs.uri`"
  )


def _NormalizeGcsUri(raw_uri: str, field_description: str) -> str:
  """Returns `raw_uri` validated as a `gs://<bucket>[/<path>]` URI.

  Args:
    raw_uri: The URI from the pipeline YAML.
    field_description: Describes the field holding `raw_uri` for error
      messages.

  Returns:
    The URI without outer whitespace or trailing slashes.

  Raises:
    errors.PipelineLoadError: If the URI does not start with `gs://`, has an
      empty path segment or one with whitespace, or names an invalid bucket.
  """
  uri = raw_uri.strip().rstrip("/")
  error_message = (
      f"{field_description} '{raw_uri}' must be a valid"
      " `gs://<bucket>[/<path>]` Cloud Storage URI"
  )
  uri_match = _GCS_URI_RE.fullmatch(uri)
  if uri_match is None:
    raise errors.PipelineLoadError(f"{error_message}.")
  try:
    storage_util.ValidateBucketUrl(uri_match.group("bucket"))
  except storage_util.InvalidNameError as e:
    raise errors.PipelineLoadError(f"{error_message}: {e}") from e
  return uri


def _VerifyNoUnsupportedKeys(
    mapping: Mapping[Any, Any],
    supported_keys: Sequence[str],
    source_description: str,
    field_name: str | None = None,
) -> None:
  """Verifies that `mapping` sets no key outside `supported_keys`.

  Args:
    mapping: The YAML mapping to check: the pipeline YAML, a data model entry,
      or a field of one of them at `field_name`. Keys need not be strings (YAML
      parses an unquoted `on:` as the boolean `True`).
    supported_keys: The keys that `runner: orchestration_service` supports in
      `mapping`.
    source_description: Description of the owner of `mapping` for error
      messages.
    field_name: Path of `mapping` in its owner, or None if `mapping` is the
      owner itself.

  Raises:
    errors.PipelineLoadError: If `mapping` sets any other key.
  """
  unsupported_keys = [key for key in mapping if key not in supported_keys]
  if unsupported_keys:
    location = f" in `{field_name}`" if field_name else ""
    raise errors.PipelineLoadError(
        f"{source_description} specifies {_FormatKeys(unsupported_keys)}"
        f"{location}, which is not supported for"
        f" `runner: {ORCHESTRATION_SERVICE_RUNNER}` yet; supported keys:"
        f" {_FormatKeys(supported_keys)}."
    )


def _FormatKeys(keys: Sequence[Any]) -> str:
  """Formats `keys` as a comma-separated list of code spans."""
  return ", ".join(f"`{key}`" for key in keys)


def _GetDbtProjectDirectory(
    dbt_config: Mapping[str, Any],
    base_directory: pathlib.Path,
    source_description: str,
) -> pathlib.Path:
  """Returns the validated dbt project directory resolved against base_directory."""
  project_directory = base_directory / _GetNonEmptyStringFromMapping(
      dbt_config, "sourcePath", f"{source_description} `dbt`"
  )
  if not project_directory.is_dir():
    raise errors.PipelineLoadError(
        f"{source_description}: dbt project directory '{project_directory}'"
        " does not exist."
    )
  return project_directory


def _GetRawDataModelsFromPipelineYaml(
    raw_pipeline_yaml: Mapping[str, Any],
) -> Any:
  """Returns the unvalidated `spec.dataPipeline.dataModels` value.

  Walks `spec` -> `dataPipeline` (the API's `Pipeline.spec` ->
  `PipelineSpec.data_pipeline`), rejecting the other `PipelineSpec` fields.

  Args:
    raw_pipeline_yaml: The pipeline YAML mapping, which defines `spec`.

  Returns:
    The `dataModels` value, or None when `dataPipeline` does not define it.

  Raises:
    errors.PipelineLoadError: If `spec` or `spec.dataPipeline` is missing, is
      not a mapping, or has unsupported keys.
  """
  spec = _GetRequiredMappingFromMapping(
      raw_pipeline_yaml, _SPEC_KEY, "Pipeline YAML"
  )
  spec_description = f"Pipeline YAML `{_SPEC_KEY}`"
  _VerifyNoUnsupportedKeys(
      spec, _SUPPORTED_SPEC_KEYS, "Pipeline YAML", _SPEC_KEY
  )
  data_pipeline = _GetRequiredMappingFromMapping(
      spec, _DATA_PIPELINE_KEY, spec_description
  )
  _VerifyNoUnsupportedKeys(
      data_pipeline,
      _SUPPORTED_DATA_PIPELINE_KEYS,
      "Pipeline YAML",
      f"{_SPEC_KEY}.{_DATA_PIPELINE_KEY}",
  )
  return data_pipeline.get(_DATA_MODELS_KEY)


def _GetDataModelsFromPipelineYaml(
    raw_pipeline_yaml: Mapping[str, Any],
    base_directory: pathlib.Path,
    project: str,
    location: str,
) -> tuple[tuple[DbtModelSpec, ...], tuple[SdpModelSpec, ...]]:
  """Parses and validates `spec.dataPipeline.dataModels`.

  Each entry has an `id`, unique within the pipeline, and exactly one of `sdp`
  or `dbt`, holding the configuration of that kind of data model (the API's
  `DataModel`). Any number of dbt data models is supported, but at most one SDP
  data model.

  Args:
    raw_pipeline_yaml: The pipeline YAML mapping.
    base_directory: Directory of the pipeline YAML; relative paths in it are
      resolved against this directory.
    project: The pipeline's project ID.
    location: The pipeline's location.

  Returns:
    `(dbt_models, sdp_models)`, each in their `dataModels` order.

  Raises:
    errors.PipelineLoadError: If `spec.dataPipeline.dataModels` or one of its
      entries is invalid.
  """
  entries_by_type = _GroupDataModelEntriesByType(
      _GetDataModelEntriesFromPipelineYaml(raw_pipeline_yaml)
  )
  sdp_entries = entries_by_type[SDP_MODEL_TYPE]
  if len(sdp_entries) > 1:
    raise errors.PipelineLoadError(
        f"Pipeline YAML `{_DATA_MODELS_KEY}` currently supports at most one"
        f" {SDP_MODEL_TYPE} data model (got {len(sdp_entries)})."
    )
  dbt_models = tuple(
      _GetDbtModelSpecFromDbtConfig(model_id, dbt_config, base_directory)
      for model_id, dbt_config in entries_by_type[DBT_MODEL_TYPE]
  )
  sdp_models = tuple(
      _GetSdpModelSpecFromSdpConfig(
          model_id, sdp_config, base_directory, project, location
      )
      for model_id, sdp_config in sdp_entries
  )
  return dbt_models, sdp_models


def _GetDataModelEntriesFromPipelineYaml(
    raw_pipeline_yaml: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
  """Returns the entries of `spec.dataPipeline.dataModels`.

  Args:
    raw_pipeline_yaml: The pipeline YAML mapping.

  Returns:
    The non-empty list of `dataModels` mappings.

  Raises:
    errors.PipelineLoadError: If `spec` is missing or invalid, `dataModels` is
      missing, empty or not a list, or one of its entries is not a mapping.
  """
  if _SPEC_KEY not in raw_pipeline_yaml:
    raise errors.PipelineLoadError(
        f"Pipeline YAML must define `{_DATA_MODELS_PATH}`."
    )
  raw_data_models = _GetRawDataModelsFromPipelineYaml(raw_pipeline_yaml)
  if raw_data_models is not None and not isinstance(raw_data_models, list):
    raise errors.PipelineLoadError(
        f"Pipeline YAML `{_DATA_MODELS_PATH}` must be a list."
    )
  if not raw_data_models:
    raise errors.PipelineLoadError(
        f"Pipeline YAML must define `{_DATA_MODELS_PATH}` with at least one"
        " entry."
    )
  if not all(isinstance(entry, Mapping) for entry in raw_data_models):
    raise errors.PipelineLoadError(
        f"Every entry in `{_DATA_MODELS_KEY}` must be a mapping."
    )
  return raw_data_models


def _GroupDataModelEntriesByType(
    entries: Sequence[Mapping[str, Any]],
) -> dict[str, list[tuple[str, Mapping[str, Any]]]]:
  """Validates the `id` and keys of each `dataModels` entry and groups them.

  Args:
    entries: The `dataModels` mappings.

  Returns:
    `(id, config)` pairs keyed by `SDP_MODEL_TYPE` and `DBT_MODEL_TYPE`, in
    `dataModels` order, where `config` is the entry's `sdp` or `dbt` mapping.

  Raises:
    errors.PipelineLoadError: If an entry has an invalid or duplicate `id`,
      sets an unsupported key, or does not set exactly one of `sdp` and `dbt`.
  """
  entries_by_type: dict[str, list[tuple[str, Mapping[str, Any]]]] = {
      SDP_MODEL_TYPE: [],
      DBT_MODEL_TYPE: [],
  }
  seen_ids: set[str] = set()
  for entry in entries:
    model_id = _GetDataModelId(entry)
    source_description = f"Data model '{model_id}'"
    _VerifyNoUnsupportedKeys(
        entry, _SUPPORTED_DATA_MODEL_KEYS, source_description
    )
    if model_id in seen_ids:
      raise errors.PipelineLoadError(
          f"Duplicate data model ID '{model_id}' in `{_DATA_MODELS_PATH}`."
      )
    seen_ids.add(model_id)
    model_type = _GetDataModelType(entry, source_description)
    entries_by_type[model_type].append((model_id, entry[model_type]))
  return entries_by_type


def _GetDataModelId(entry: Mapping[str, Any]) -> str:
  """Returns the validated `id` of a `dataModels` entry.

  Args:
    entry: One `dataModels` mapping.

  Returns:
    The data model ID.

  Raises:
    errors.PipelineLoadError: If `id` is missing or does not satisfy
      `_MODEL_ID_RULE`.
  """
  model_id = _GetNonEmptyStringFromMapping(
      entry, "id", f"A `{_DATA_MODELS_KEY}` entry"
  )
  if not _MODEL_ID_RE.fullmatch(model_id):
    raise errors.PipelineLoadError(
        f"Data model id '{model_id}' {_MODEL_ID_RULE}."
    )
  return model_id


def _GetDataModelType(entry: Mapping[str, Any], source_description: str) -> str:
  """Returns the kind of a `dataModels` entry: the one of `sdp`/`dbt` it sets.

  Args:
    entry: One `dataModels` mapping.
    source_description: Describes the entry for error messages.

  Returns:
    `SDP_MODEL_TYPE` or `DBT_MODEL_TYPE`.

  Raises:
    errors.PipelineLoadError: If the entry sets neither or both of `sdp` and
      `dbt`, or the one it sets is not a mapping.
  """
  present_types = [
      model_type
      for model_type in (SDP_MODEL_TYPE, DBT_MODEL_TYPE)
      if entry.get(model_type) is not None
  ]
  if len(present_types) != 1:
    raise errors.PipelineLoadError(
        f"{source_description} must define exactly one of `{SDP_MODEL_TYPE}`"
        f" or `{DBT_MODEL_TYPE}`."
    )
  model_type = present_types[0]
  if not isinstance(entry[model_type], Mapping):
    raise errors.PipelineLoadError(
        f"{source_description}: `{model_type}` must be a Mapping."
    )
  return model_type


def _GetDbtModelSpecFromDbtConfig(
    model_id: str,
    dbt_config: Mapping[str, Any],
    base_directory: pathlib.Path,
) -> DbtModelSpec:
  """Parses and validates the `dbt` mapping of a `dataModels` entry.

  Args:
    model_id: The validated `id` of the data model.
    dbt_config: The entry's `dbt` mapping.
    base_directory: Directory of the pipeline YAML, against which `sourcePath`
      is resolved.

  Returns:
    The dbt data model with ID `model_id`.

  Raises:
    errors.PipelineLoadError: If `dbt_config` sets an unsupported key, or its
      `sourcePath`, `managedRuntime` or `profileConfig` is invalid.
  """
  source_description = f"Data model '{model_id}'"
  _VerifyNoUnsupportedKeys(
      dbt_config, _SUPPORTED_DBT_KEYS, source_description, DBT_MODEL_TYPE
  )
  return DbtModelSpec(
      id=model_id,
      project_directory=_GetDbtProjectDirectory(
          dbt_config, base_directory, source_description
      ),
      dbt_version=_GetDbtVersionFromConfig(dbt_config, source_description),
      profile_config=dict(
          _GetTypedFieldFromMapping(
              dbt_config,
              "profileConfig",
              Mapping,
              f"{source_description} `dbt`",
              default={},
          )
      ),
  )


def _GetDbtVersionFromConfig(
    dbt_config: Mapping[str, Any], source_description: str
) -> str:
  """Returns the validated `managedRuntime.dbtVersion` of a dbt data model.

  Args:
    dbt_config: The `dbt` mapping of a `dataModels` entry.
    source_description: Describes the data model for error messages.

  Returns:
    The version of the Google-managed dbt runtime, e.g. `1.9`.

  Raises:
    errors.PipelineLoadError: If `managedRuntime` is missing, is not a mapping
      or sets an unsupported key, or `dbtVersion` is not a non-empty string.
  """
  managed_runtime = _GetRequiredMappingFromMapping(
      dbt_config, "managedRuntime", f"{source_description} `dbt`"
  )
  _VerifyNoUnsupportedKeys(
      managed_runtime,
      _SUPPORTED_MANAGED_RUNTIME_KEYS,
      source_description,
      "dbt.managedRuntime",
  )
  # Must be quoted in YAML: `dbtVersion: 1.10` would parse as the float 1.1.
  return _GetNonEmptyStringFromMapping(
      managed_runtime,
      "dbtVersion",
      f"{source_description} `dbt.managedRuntime`",
  )


def _GetSdpModelSpecFromSdpConfig(
    model_id: str,
    sdp_config: Mapping[str, Any],
    base_directory: pathlib.Path,
    project: str,
    location: str,
) -> SdpModelSpec:
  """Parses and validates the `sdp` mapping of a `dataModels` entry."""
  source_description = f"Data model '{model_id}'"
  _VerifyNoUnsupportedKeys(
      sdp_config, _SUPPORTED_SDP_KEYS, source_description, SDP_MODEL_TYPE
  )
  spec_path = _ResolveSdpSpecPath(
      sdp_config, base_directory, source_description
  )
  return SdpModelSpec(
      id=model_id,
      project_directory=spec_path.parent,
      spec_path=spec_path,
      execution_config=_GetSdpExecutionConfigFromSdpConfig(
          sdp_config, source_description, project, location
      ),
  )


def _ResolveSdpSpecPath(
    sdp_config: Mapping[str, Any],
    base_directory: pathlib.Path,
    source_description: str,
) -> pathlib.Path:
  """Resolves `specPath`, or auto-discovers `spark-pipeline.yml`."""
  raw_spec_path = _GetTypedFieldFromMapping(
      sdp_config, "specPath", str, source_description
  )
  if raw_spec_path is None:
    return _AutoDiscoverSdpSpecPath(
        base_directory.resolve(), source_description
    )
  if not raw_spec_path.strip():
    raise errors.PipelineLoadError(
        f"{source_description}: `specPath` must not be empty."
    )
  return _ResolveLocalPathWithinBase(
      raw_spec_path, base_directory, "specPath", source_description
  )


def _AutoDiscoverSdpSpecPath(
    project_directory: pathlib.Path, source_description: str
) -> pathlib.Path:
  """Auto-discovers `spark-pipeline.yml` or `.yaml` in `project_directory`."""
  found: list[pathlib.Path] = []
  for name in _SDP_SPEC_CANDIDATES:
    candidate = project_directory / name
    if candidate.is_symlink():
      raise errors.PipelineLoadError(
          f"{source_description}: auto-discovered `{candidate.name}`"
          f" '{candidate}' is a symlink; set `specPath` to a regular file."
      )
    if candidate.is_file():
      found.append(candidate)
  candidate_names = " or ".join(f"`{name}`" for name in _SDP_SPEC_CANDIDATES)
  if len(found) > 1:
    found_names = " and ".join(f"`{path.name}`" for path in found)
    raise errors.PipelineLoadError(
        f"{source_description}: both {found_names} exist in"
        f" '{project_directory}'; specify `specPath` explicitly."
    )
  if len(found) == 1:
    return found[0].resolve()
  raise errors.PipelineLoadError(
      f"{source_description}: `specPath` was not specified and no"
      f" {candidate_names} was found in '{project_directory}'."
  )


def _ResolveLocalPathWithinBase(
    raw_path: str,
    base_directory: pathlib.Path,
    field_name: str,
    source_description: str,
) -> pathlib.Path:
  """Resolves `raw_path` under `base_directory`, rejecting symlinks/escapes.

  Applies to the individual files an SDP data model references (`specPath`),
  which are uploaded as-is. A dbt `sourcePath` is validated by the dbt packager
  instead, which walks the directory contents.

  Args:
    raw_path: The path from `pipeline.yaml`, relative to `base_directory`.
    base_directory: The directory containing `pipeline.yaml`.
    field_name: The `pipeline.yaml` key holding `raw_path`, for error messages.
    source_description: Describes the data model for error messages.

  Returns:
    The resolved absolute path of the regular file.

  Raises:
    errors.PipelineLoadError: If the path escapes `base_directory`, is a
      symlink, does not exist, or is not a regular file.
  """
  candidate = base_directory / raw_path
  _VerifyPathDoesNotTraverseOutsideBase(
      candidate, base_directory, field_name, source_description
  )
  if candidate.is_symlink():
    raise errors.PipelineLoadError(
        f"{source_description}: `{field_name}` '{candidate}' must not be a"
        " symlink."
    )
  if not candidate.exists():
    raise errors.PipelineLoadError(
        f"{source_description}: `{field_name}` '{candidate}' does not exist."
    )
  if not candidate.is_file():
    raise errors.PipelineLoadError(
        f"{source_description}: `{field_name}` '{candidate}' is not a regular"
        " file."
    )
  return candidate.resolve()


def _VerifyPathDoesNotTraverseOutsideBase(
    target_path: pathlib.Path,
    base_directory: pathlib.Path,
    field_name: str,
    source_description: str,
) -> None:
  """Raises `PipelineLoadError` if a path escapes the pipeline directory."""
  try:
    target_path.resolve().relative_to(base_directory.resolve())
  except ValueError as e:
    raise errors.PipelineLoadError(
        f"{source_description}: `{field_name}` '{target_path}' escapes the"
        f" pipeline directory '{base_directory}'."
    ) from e


def _GetSdpExecutionConfigFromSdpConfig(
    sdp_config: Mapping[str, Any],
    source_description: str,
    project: str,
    location: str,
) -> SdpExecutionConfig:
  """Parses and validates `executionConfig` of an SDP data model."""
  raw_config = _GetTypedFieldFromMapping(
      sdp_config, "executionConfig", Mapping, source_description, default={}
  )
  config_description = f"{source_description} `executionConfig`"
  _VerifyNoUnsupportedKeys(
      raw_config,
      _SUPPORTED_EXECUTION_CONFIG_KEYS,
      source_description,
      "executionConfig",
  )
  subnetwork = _GetOptionalNonEmptyStringFromMapping(
      raw_config, "subnetwork", config_description
  )
  if subnetwork is not None:
    subnetwork = _ResolveSubnetworkName(
        subnetwork, project, location, source_description
    )
  return SdpExecutionConfig(
      jar_uris=_GetJarUris(raw_config, config_description),
      subnetwork=subnetwork,
      properties=_GetStringDictFromMapping(
          raw_config, "properties", config_description
      ),
  )


def _GetJarUris(
    raw_config: Mapping[str, Any], config_description: str
) -> tuple[str, ...]:
  """Returns the validated, de-duplicated `gs://` URIs of `jarUris`."""
  raw_jar_uris = _GetTypedFieldFromMapping(
      raw_config, "jarUris", list, config_description, default=[]
  )
  jar_uris: list[str] = []
  for raw_jar_uri in raw_jar_uris:
    jar_uri = _GetJarUri(raw_jar_uri, config_description)
    if jar_uri in jar_uris:
      raise errors.PipelineLoadError(
          f"{config_description}: `jarUris` lists '{jar_uri}' more than once."
      )
    jar_uris.append(jar_uri)
  return tuple(jar_uris)


def _GetJarUri(raw_jar_uri: Any, config_description: str) -> str:
  """Returns `raw_jar_uri` validated as a `gs://<bucket>/<path>.jar` URI.

  Bucket and object names are checked by `storage_util`, which applies the
  Cloud Storage naming rules (3-63 characters without dots, up to 222 with).

  Args:
    raw_jar_uri: One `jarUris` list item from `pipeline.yaml`.
    config_description: Describes the `executionConfig` for error messages.

  Returns:
    The stripped URI.

  Raises:
    errors.PipelineLoadError: If the item is not a string, not a valid Cloud
      Storage object URI, or does not end in `.jar`.
  """
  jar_uri = raw_jar_uri.strip() if isinstance(raw_jar_uri, str) else ""
  error_message = (
      f"{config_description}: `jarUris` must list `gs://<bucket>/<path>.jar`"
      f" URIs (got '{raw_jar_uri}')"
  )
  try:
    object_ref = storage_util.ObjectReference.FromUrl(jar_uri)
  except ValueError as e:
    raise errors.PipelineLoadError(f"{error_message}: {e}") from e
  if not object_ref.name.endswith(".jar"):
    raise errors.PipelineLoadError(f"{error_message}.")
  return jar_uri


def _ResolveSubnetworkName(
    subnetwork: str, project: str, location: str, source_description: str
) -> str:
  """Expands a bare `executionConfig.subnetwork` name to a full resource name.

  The Orchestration API only accepts
  `projects/<project>/regions/<region>/subnetworks/<subnetwork>`. For parity
  with `gcloud dataproc batches submit --subnet`, which accepts a bare name, a
  bare name is expanded with the pipeline's project and location; any other
  partial path is rejected here instead of by the API.

  Args:
    subnetwork: The `executionConfig.subnetwork` value from `pipeline.yaml`.
    project: The pipeline's project ID.
    location: The pipeline's location (Compute Engine region).
    source_description: Describes the data model for error messages.

  Returns:
    The fully qualified subnetwork resource name.

  Raises:
    errors.PipelineLoadError: If `subnetwork` is neither a bare name nor a full
      resource name.
  """
  if _SUBNETWORK_NAME_RE.fullmatch(subnetwork):
    return subnetwork
  if "/" in subnetwork:
    raise errors.PipelineLoadError(
        f"{source_description}: `executionConfig.subnetwork` '{subnetwork}'"
        " must be a subnetwork name in the pipeline's project and location, or"
        " a full resource name"
        " (`projects/<project>/regions/<region>/subnetworks/<subnetwork>`),"
        " which is required for Shared VPC subnetworks."
    )
  # A bare name is assumed to live in the pipeline's own project; Shared VPC
  # subnetworks live in the host project and need the full resource name.
  return f"projects/{project}/regions/{location}/subnetworks/{subnetwork}"


def _GetEnvironmentModelFromDeploymentFile(
    environment_name: str | None,
    deployment_file_path: pathlib.Path | None,
    external_variables: Mapping[str, Any],
) -> deployment_model.EnvironmentModel | None:
  """Loads the `--environment` environment of `deployment.yaml`.

  Args:
    environment_name: The target environment (`--environment`), or None when
      it is not set, in which case `deployment_file_path` is None as well.
    deployment_file_path: Path to `deployment.yaml`, or None when the pipeline
      is deployed without one.
    external_variables: The variables from `_CollectExternalVariables`, which
      `yaml_processor` uses to resolve the `{{ }}` tags of `deployment.yaml`.

  Returns:
    The validated environment, or None when `deployment_file_path` is None.

  Raises:
    errors.PipelineLoadError: If the environment is missing or invalid, or sets
      a Cloud Composer-only field.
  """
  if deployment_file_path is None:
    return None
  try:
    _, _, environment = yaml_processor.parse_deployment(
        str(deployment_file_path),
        environment_name,
        dict(external_variables),
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
    environment_name: str | None,
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
      defaults, "projectId", f"{source_description} `defaults`"
  )
  _LogIgnoredPipelineValue(
      "defaults.projectId", default_project, environment_project
  )
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
      defaults, "location", f"{source_description} `defaults`"
  )
  _LogIgnoredPipelineValue(
      "defaults.location", default_location, environment_location
  )
  location = environment_location or default_location
  if not location or not location.strip():
    raise errors.PipelineLoadError(
        "Location must be set via `deployment.yaml` (`region`) or"
        " `defaults.location`."
    )
  return location


def _LogIgnoredPipelineValue(
    yaml_path: str,
    pipeline_value: str | None,
    environment_value: str | None,
) -> None:
  """Logs when `deployment.yaml` overrides a different `pipeline.yaml` value."""
  if (
      pipeline_value
      and environment_value
      and pipeline_value != environment_value
  ):
    log.info(
        "Using '%s' from `deployment.yaml`; `%s: %s` in `pipeline.yaml` is"
        " ignored.",
        environment_value,
        yaml_path,
        pipeline_value,
    )


def _GetServiceAccountEmail(
    environment: deployment_model.EnvironmentModel | None,
    raw_pipeline_yaml: Mapping[str, Any],
    source_description: str,
) -> str:
  """Returns the pipeline execution service account email.

  `deployment.yaml` `service_account` takes precedence over the pipeline's
  `executionIdentity.serviceAccount.email`. The Orchestration service
  rejects pipelines without an execution identity, so one of them is
  required.

  Args:
    environment: The `deployment.yaml` environment, or None without one.
    raw_pipeline_yaml: The pipeline YAML mapping.
    source_description: Describes the pipeline YAML for error messages.

  Returns:
    The service account email.

  Raises:
    errors.PipelineLoadError: If neither source sets a service account, or
      `executionIdentity` is malformed.
  """
  environment_service_account = (
      environment.service_account if environment else None
  )
  pipeline_service_account = _GetExecutionIdentityEmailFromPipelineYaml(
      raw_pipeline_yaml, source_description
  )
  _LogIgnoredPipelineValue(
      _SERVICE_ACCOUNT_EMAIL_PATH,
      pipeline_service_account,
      environment_service_account,
  )
  service_account = environment_service_account or pipeline_service_account
  if not service_account or not service_account.strip():
    raise errors.PipelineLoadError(
        "Service account must be set via `deployment.yaml`"
        f" (`service_account`) or `{_SERVICE_ACCOUNT_EMAIL_PATH}`; the"
        " Orchestration service runs the pipeline as this account."
    )
  return service_account


def _GetExecutionIdentityEmailFromPipelineYaml(
    raw_pipeline_yaml: Mapping[str, Any], source_description: str
) -> str | None:
  """Returns `executionIdentity.serviceAccount.email`, or None when unset.

  `executionIdentity` mirrors the API's `Pipeline.execution_identity`; only the
  `serviceAccount` arm of its `identity` oneof can be set by the CLI.

  Args:
    raw_pipeline_yaml: The pipeline YAML mapping.
    source_description: Describes the pipeline YAML for error messages.

  Returns:
    The non-empty email, or None when `executionIdentity` is absent or null.

  Raises:
    errors.PipelineLoadError: If `executionIdentity` is present but is not a
      mapping holding exactly `serviceAccount: {email: <non-empty string>}`.
  """
  execution_identity = _GetTypedFieldFromMapping(
      raw_pipeline_yaml, _EXECUTION_IDENTITY_KEY, Mapping, source_description
  )
  if execution_identity is None:
    return None
  identity_description = f"{source_description} `{_EXECUTION_IDENTITY_KEY}`"
  _VerifyNoUnsupportedKeys(
      execution_identity,
      _SUPPORTED_EXECUTION_IDENTITY_KEYS,
      source_description,
      _EXECUTION_IDENTITY_KEY,
  )
  service_account = _GetRequiredMappingFromMapping(
      execution_identity, "serviceAccount", identity_description
  )
  service_account_description = f"{identity_description} `serviceAccount`"
  _VerifyNoUnsupportedKeys(
      service_account,
      _SUPPORTED_SERVICE_ACCOUNT_IDENTITY_KEYS,
      source_description,
      f"{_EXECUTION_IDENTITY_KEY}.serviceAccount",
  )
  return _GetNonEmptyStringFromMapping(
      service_account, "email", service_account_description
  )


def _GetArtifactBucketAndPathPrefix(
    environment: deployment_model.EnvironmentModel | None,
    project: str,
    location: str,
) -> tuple[str, str]:
  """Returns `(artifact_bucket, artifact_path_prefix)` for the deployment."""
  artifact_storage = environment.artifact_storage if environment else None
  if artifact_storage:
    return (
        _GetArtifactBucketName(artifact_storage.bucket),
        artifact_storage.path_prefix or "",
    )
  project_number = _GetProjectNumber(project)
  return f"dcs-artifacts-{project_number}-{location}", ""


def _GetArtifactBucketName(bucket: str) -> str:
  """Returns `artifact_storage.bucket` without outer whitespace.

  `yaml_processor` accepts a `/` in the bucket name, but callers build
  `gs://<bucket>/<object>` URIs from it, so e.g. `my-bucket/` would yield `//`.

  Args:
    bucket: `artifact_storage.bucket` of `deployment.yaml`.

  Raises:
    errors.PipelineLoadError: If `bucket` contains a `/`.
  """
  bucket_name = bucket.strip()
  if "/" in bucket_name:
    raise errors.PipelineLoadError(
        f"`artifact_storage.bucket` '{bucket}' of `deployment.yaml` cannot"
        " contain `/`; set only the bucket name, e.g. 'my-bucket', and put"
        " object paths in `artifact_storage.path_prefix`."
    )
  return bucket_name


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
