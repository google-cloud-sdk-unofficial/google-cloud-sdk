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
"""Utilities for performing local builds using universal-maker."""

import json
import os
import os.path
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files

_LOCAL_BUILD_LOG_FILENAME = 'gcloud_local_build.log'


class LocalBuildFailedError(c_exceptions.ToolException):
  """Raised when universal-maker execution fails during a local build."""


def _NoUnsupportedFiles(source_dir: str, filenames: List[str]) -> bool:
  """Checks if any unsupported configuration file exists.

  Args:
    source_dir: str, path to the source directory.
    filenames: list[str], names of files to check (e.g. ['Dockerfile',
      'project.toml']).

  Returns:
    bool: True if local build can proceed.

  Raises:
    c_exceptions.InvalidArgumentException: If an unsupported file exists.
  """
  for filename in filenames:
    file_path = os.path.join(source_dir, filename)
    if os.path.exists(file_path):
      if filename == 'Dockerfile':
        extra_remedy = (
            ', or build your container image locally using Docker and deploy'
            ' using --image'
        )
      elif filename == 'project.toml':
        extra_remedy = (
            ', or build your container image locally using Buildpacks (`pack'
            ' build`) and deploy using --image'
        )
      else:
        extra_remedy = ''
      raise c_exceptions.InvalidArgumentException(
          '--local-build',
          'Local builds (--local-build) are not supported for {} based'
          ' applications. To deploy this application, use standard source'
          ' deployment without --local-build for a server-side Cloud Build{}.'
          .format(filename, extra_remedy),
      )
  return True


def ValidateLocalBuildSource(source_dir: str) -> bool:
  """Validates that local build can be performed on the source directory.

  Checks for unsupported files like Dockerfile and project.toml.
  For these files, prompts the user to fallback if interactive.

  Args:
    source_dir: str, path to the source directory.

  Returns:
    bool: True if local build should proceed, False if user chose to fallback
      to server-side build.

  Raises:
    c_exceptions.InvalidArgumentException: If unsupported files exist and cannot
      fallback.
    c_exceptions.ToolException: If source_dir is missing.
  """
  if not source_dir:
    raise c_exceptions.ToolException(
        'Source directory must be specified for local builds.'
    )

  return _NoUnsupportedFiles(source_dir, ['Dockerfile', 'project.toml'])


def GetUniversalMakerPath() -> str:
  """Ensures universal-maker is installed and returns its path.

  Returns:
    str: The absolute path to the universal-maker binary.

  Raises:
    c_exceptions.ToolException: If the SDK root or binary is not found.
  """
  env_maker_path = encoding.GetEncodedValue(os.environ, 'UNIVERSAL_MAKER_PATH')
  if env_maker_path and os.path.isfile(env_maker_path):
    return env_maker_path

  update_manager.UpdateManager.EnsureInstalledAndRestart(['universal-maker'])
  sdk_root = config.Paths().sdk_root
  if not sdk_root:
    raise c_exceptions.ToolException('Could not find SDK root directory.')
  sdk_bin_dir = os.path.join(sdk_root, 'bin')
  maker_path = files.FindExecutableOnPath('universal-maker', path=sdk_bin_dir)
  if not maker_path:
    raise c_exceptions.ToolException(
        'universal-maker binary not found in {}.'.format(sdk_bin_dir)
    )
  return maker_path


def RunUniversalMaker(
    maker_path: str, source_dir: str, tracker: Optional[Any] = None
) -> Dict[str, Any]:
  """Runs universal-maker on the source directory and returns the parsed output.

  Args:
    maker_path: str, path to the universal-maker binary.
    source_dir: str, path to the source directory.
    tracker: ProgressTracker, optional progress tracker to display log links.

  Returns:
    dict: The parsed build_output.json contents.

  Raises:
    LocalBuildFailedError: If universal-maker execution fails.
    c_exceptions.ToolException: If process launch or JSON parsing fails.
  """
  log_file_path = os.path.join(tempfile.gettempdir(), _LOCAL_BUILD_LOG_FILENAME)
  log_msg = 'Logs are available at [ file://{} ].'.format(log_file_path)
  if tracker:
    tracker.UpdateStage(stages.LOCAL_BUILD_STAGE_KEY, log_msg)
  else:
    log.status.Print(log_msg)

  with tempfile.TemporaryDirectory() as temp_dir:
    cmd = [
        maker_path,
        '-application_dir',
        source_dir,
        '-output_dir',
        temp_dir,
        '-target_platform',
        'linux/amd64',
    ]

    try:
      with files.FileWriter(log_file_path) as log_file:
        log_file.write('--- Universal Maker Build Logs ---\n')
        log_file.flush()
        with metrics.RecordDuration('local_build'):
          result = subprocess.run(
              cmd, stdout=log_file, stderr=subprocess.STDOUT, check=False
          )
          if getattr(result, 'stdout', None):
            log_file.write(str(result.stdout))
          if getattr(result, 'stderr', None):
            log_file.write(str(result.stderr))
    except Exception as e:
      try:
        with files.FileWriter(log_file_path, append=True) as log_file:
          log_file.write('\n--- Subprocess Execution Error ---\n{}\n'.format(e))
      except Exception:  # pylint: disable=broad-exception-caught
        pass
      raise c_exceptions.ToolException(
          'Failed to execute universal-maker: {}'.format(e)
      )

    if result.returncode != 0:
      raise LocalBuildFailedError(
          'Local build execution failed. Please check the build logs at'
          ' file://{}.\nTo deploy this application without a local build, use'
          ' standard source deployment (e.g., remove --local-build from your'
          ' command) for a server-side Cloud Build, or build your container'
          ' image locally using Docker/Pack and deploy it using --image.'
          .format(log_file_path)
      )

    output_json_path = os.path.join(temp_dir, 'build_output.json')
    if not os.path.exists(output_json_path):
      raise c_exceptions.ToolException(
          'Universal Maker succeeded but did not generate build_output.json.'
      )

    try:
      with files.FileReader(output_json_path) as f:
        return json.load(f)
    except Exception as e:
      raise c_exceptions.ToolException(
          'Failed to parse build_output.json: {}'.format(e)
      )


def WarnOrPromptOnBaseImageMismatch(
    inferred_runtime: str, base_image: str
) -> None:
  """Prompts or warns the user when explicit base image differs from local runtime.

  Args:
    inferred_runtime: str, the runtime version detected by local build.
    base_image: str, the explicitly provided base image flag value.

  Raises:
    c_exceptions.ToolException: If interactive prompt is declined by user.
  """
  if not inferred_runtime or not base_image or base_image == inferred_runtime:
    return

  message = (
      "Local build is executing using your host's {} environment, but you have"
      ' overridden the runtime base image to {}. This may cause ABI version'
      ' mismatches at runtime if your project compiles native binary'
      ' dependencies.'.format(inferred_runtime, base_image)
  )

  if console_io.CanPrompt():
    if not console_io.PromptContinue(
        message=message, prompt_string='Do you want to proceed', default=True
    ):
      raise c_exceptions.ToolException('Aborted by user.')
  else:
    log.warning(
        "Local build is executing using your host's %s environment, but you"
        ' have overridden the runtime base image to %s. This may cause ABI'
        ' version mismatches at runtime if your project compiles native binary'
        ' dependencies.',
        inferred_runtime,
        base_image,
    )


def PerformLocalBuild(
    container_name: str,
    container_args: Any,
    local_build_dir: str,
    maker_path: Optional[str] = None,
    tracker: Optional[Any] = None,
) -> Tuple[List[Any], str, Optional[str]]:
  """Orchestrates the local build flow in an isolated temporary directory.

  Args:
    container_name: str, name of the container being built (empty for primary).
    container_args: argparse.Namespace, the container-level arguments.
    local_build_dir: the directory to use for the local build.
    maker_path: str, optional path to the universal-maker binary.
    tracker: ProgressTracker, optional progress tracker for status display.

  Returns:
    tuple: (local_build_changes, local_build_base_image,
    inferred_runtime)
      - local_build_changes (list): The list of ConfigChanger objects to
      apply.
      - local_build_base_image (str): The inferred base image runtime.
      - inferred_runtime (str): The runtime version detected by universal-maker.

  Raises:
    LocalBuildFailedError: If build execution fails.
    c_exceptions.InvalidArgumentException: If local build is not supported.
    c_exceptions.ToolException: If copy or JSON parsing fails.
  """
  source_dir = container_args.source
  ValidateLocalBuildSource(source_dir)

  if not maker_path:
    maker_path = GetUniversalMakerPath()

  try:
    shutil.copytree(
        source_dir,
        local_build_dir,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns('.git', '.hg', '.svn'),
    )
  except Exception as e:
    raise c_exceptions.ToolException(
        'Failed to copy source directory to temporary build directory: {}'
        .format(e)
    )

  try:
    build_output = RunUniversalMaker(
        maker_path, local_build_dir, tracker=tracker
    )
  except LocalBuildFailedError as e:
    if tracker:
      tracker.FailStage(
          stages.LOCAL_BUILD_STAGE_KEY,
          e,
          message=(
              'Local build failed and logs are available at [ file://{} ].'
              .format(
                  os.path.join(tempfile.gettempdir(), _LOCAL_BUILD_LOG_FILENAME)
              )
          ),
      )
    else:
      log.error(e)
    raise

  inferred_command = build_output.get('command')
  # build_output can contain explicit null values for 'args' and 'envVars'
  # which parse as None. Using 'or' ensures they default to empty iterables.
  inferred_args = build_output.get('args') or []
  inferred_runtime = build_output.get('runtime')
  inferred_env_vars = build_output.get('envVars') or {}

  if not inferred_runtime:
    raise c_exceptions.ToolException(
        'Universal Maker did not detect a valid runtime.'
    )

  local_build_changes = []

  # Apply inferred command and args atomically (Approach B).
  # If the user explicitly sets --command, it suppresses inferred args
  # to match standard OCI semantics (overriding ENTRYPOINT clears CMD).
  if not flags.FlagIsExplicitlySet(container_args, 'command'):
    if inferred_command:
      local_build_changes.append(
          config_changes.ContainerCommandChange(
              [inferred_command], container_name=container_name
          )
      )
    if inferred_args and not flags.FlagIsExplicitlySet(container_args, 'args'):
      local_build_changes.append(
          config_changes.ContainerArgsChange(
              inferred_args, container_name=container_name
          )
      )

  # Filter out inferred env vars that are explicitly overridden on the CLI
  cli_env_vars = {}
  for flag in ('set_env_vars', 'update_env_vars'):
    val = getattr(container_args, flag, None)
    if val:
      cli_env_vars.update(val)

  cli_removed_vars = set(getattr(container_args, 'remove_env_vars', []) or [])

  filtered_env_vars = {
      k: v
      for k, v in inferred_env_vars.items()
      if k not in cli_env_vars and k not in cli_removed_vars
  }

  if filtered_env_vars:
    local_build_changes.append(
        config_changes.EnvVarLiteralChanges(
            updates=filtered_env_vars,
            clear_others=False,
            container_name=container_name,
        )
    )

  if not flags.FlagIsExplicitlySet(container_args, 'base_image'):
    local_build_base_image = inferred_runtime
    local_build_changes.append(
        config_changes.BaseImagesAnnotationChange(
            updates={container_name: inferred_runtime}
        )
    )
  else:
    local_build_base_image = container_args.base_image

  # Redirect the source directory to our built temporary directory
  container_args.source = local_build_dir

  # Log inferred metadata ONLY if it is actually applied (not overridden)
  log.debug('Inferred runtime: %s', inferred_runtime)
  if inferred_command and not flags.FlagIsExplicitlySet(
      container_args, 'command'
  ):
    cmd_str = ' '.join([inferred_command] + (inferred_args or []))
    log.debug('Inferred entrypoint: %s', cmd_str)
  if filtered_env_vars:
    vars_str = ', '.join(f'{k}={v}' for k, v in filtered_env_vars.items())
    log.debug('Inferred environment variables: %s', vars_str)

  return local_build_changes, local_build_base_image, inferred_runtime
