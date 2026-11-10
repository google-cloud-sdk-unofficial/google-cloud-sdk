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
"""Shared utilities for tools packaged in the `bqms` Cloud SDK component."""

import os
import shlex

from googlecloudsdk.command_lib.util import java
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core.updater import local_state
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import platforms

BQMS_COMPONENT_ID = 'bqms'
BQMS_LAUNCHER_NAME = 'bqms'
BQMS_WINDOWS_LAUNCHER_NAME = 'bqms.cmd'
MIN_JAVA_VERSION = 11
# Default JVM flags for `bqms` component JARs (b/573269161): open `java.nio`
# for Apache Arrow / Netty, which Java 16+ (JEP 396) encapsulates by default,
# and pin the JVM timezone to UTC so timestamps are consistent.
DEFAULT_JVM_FLAGS = (
    '--add-opens=java.base/java.nio=ALL-UNNAMED',
    '-Duser.timezone=UTC',
)
# Extra JVM options, e.g. `JAVA_OPTS=-Xmx4G`. This is the variable the
# standalone BQMS tools' documentation tells users to set for heap size,
# Kerberos and trust-store settings.
JAVA_OPTS_ENV_VAR = 'JAVA_OPTS'


class BqmsJarNotFoundError(exceptions.Error):
  """Raised when a `bqms` component JAR file cannot be found."""


class BqmsLauncherNotFoundError(exceptions.Error):
  """Raised when the `bqms` component launcher script cannot be found."""


class InvalidJavaOptsError(exceptions.Error):
  """Raised when the `JAVA_OPTS` environment variable cannot be parsed."""


class BqmsToolExecutionError(exceptions.Error):
  """Raised when a tool of the `bqms` component exits with a non-zero status."""


def EnsureBqmsComponentInstalled(for_text):
  """Ensures that the `bqms` Cloud SDK component is installed.

  Args:
    for_text: str, Human-readable name of the tool requiring the component (e.g.
      'BigQuery Migration Extractor').

  Raises:
    local_state.InvalidSDKRootError: If a Cloud SDK installation is not found.
  """
  msg = 'You need the [{}] component to use the {}.'.format(
      BQMS_COMPONENT_ID, for_text
  )
  update_manager.UpdateManager.EnsureInstalledAndRestart(
      [BQMS_COMPONENT_ID], msg=msg
  )


def _FindComponentFile(for_text, candidates):
  """Finds the first existing file in `candidates` under the Cloud SDK root.

  Args:
    for_text: str, Human-readable name of the tool requiring the component.
    candidates: Sequence[str], Relative candidate paths under `<sdk_root>`.

  Returns:
    tuple[str or None, str], `(found_path, expected_default_path)`.

  Raises:
    local_state.InvalidSDKRootError: If no Cloud SDK root directory is found.
  """
  EnsureBqmsComponentInstalled(for_text)
  sdk_root = config.Paths().sdk_root
  if not sdk_root:
    raise local_state.InvalidSDKRootError()
  expected_path = os.path.join(sdk_root, candidates[0])
  for rel_path in candidates:
    candidate = os.path.join(sdk_root, rel_path)
    if os.path.isfile(candidate):
      return candidate, expected_path
  return None, expected_path


def GetBqmsJarPath(jar_name, for_text, env_var=None):
  """Resolves the path to a JAR file in the `bqms` Cloud SDK component.

  Checks `env_var` first (when provided), then ensures the `bqms` component is
  installed and looks under `<sdk_root>/platform/bqms/lib/<jar_name>` (or
  `<sdk_root>/platform/bqms/<jar_name>`).

  Args:
    jar_name: str, Filename of the JAR (e.g. `dumper.jar` or
      `validation-client.jar`).
    for_text: str, Human-readable name of the tool requiring the JAR (used in
      component installation prompts).
    env_var: str or None, Optional environment variable name that overrides the
      packaged JAR path.

  Returns:
    str, Path to the resolved JAR file.

  Raises:
    local_state.InvalidSDKRootError: If no Cloud SDK root directory is found.
    BqmsJarNotFoundError: If the JAR file does not exist on disk.
  """
  if env_var:
    env_jar_path = encoding.GetEncodedValue(os.environ, env_var)
    if env_jar_path:
      if not os.path.isfile(env_jar_path):
        raise BqmsJarNotFoundError(
            'JAR file [{}] specified by {} was not found at [{}].'.format(
                jar_name, env_var, env_jar_path
            )
        )
      return env_jar_path

  candidates = (
      os.path.join('platform', BQMS_COMPONENT_ID, 'lib', jar_name),
      os.path.join('platform', BQMS_COMPONENT_ID, jar_name),
  )
  found_path, expected_path = _FindComponentFile(for_text, candidates)
  if found_path:
    return found_path

  env_hint = ' or setting {}'.format(env_var) if env_var else ''
  raise BqmsJarNotFoundError(
      'JAR file [{jar_name}] was not found at [{path}]. Try reinstalling the'
      ' [{component}] component (`gcloud components reinstall {component}`)'
      '{env_hint}.'.format(
          jar_name=jar_name,
          path=expected_path,
          component=BQMS_COMPONENT_ID,
          env_hint=env_hint,
      )
  )


def GetBqmsLauncherPath(for_text):
  """Resolves the path to the `bqms` Cloud SDK component launcher script.

  Ensures the `bqms` component is installed and looks under
  `<sdk_root>/platform/bqms/bin/<launcher>` (or `<sdk_root>/bin/<launcher>`),
  where `<launcher>` is `bqms.cmd` on Windows and `bqms` on other platforms.

  Args:
    for_text: str, Human-readable name of the tool requiring the launcher (used
      in component installation prompts).

  Returns:
    str, Path to the resolved launcher script.

  Raises:
    local_state.InvalidSDKRootError: If no Cloud SDK root directory is found.
    BqmsLauncherNotFoundError: If the launcher script does not exist on disk.
  """
  launcher_name = (
      BQMS_WINDOWS_LAUNCHER_NAME
      if platforms.OperatingSystem.IsWindows()
      else BQMS_LAUNCHER_NAME
  )
  candidates = (
      os.path.join('platform', BQMS_COMPONENT_ID, 'bin', launcher_name),
      os.path.join('bin', launcher_name),
  )
  found_path, expected_path = _FindComponentFile(for_text, candidates)
  if found_path:
    return found_path

  raise BqmsLauncherNotFoundError(
      'Launcher [{launcher_name}] was not found at [{path}]. Try reinstalling'
      ' the [{component}] component (`gcloud components reinstall'
      ' {component}`).'.format(
          launcher_name=launcher_name,
          path=expected_path,
          component=BQMS_COMPONENT_ID,
      )
  )


def GetUserJvmOpts():
  """Returns extra JVM options from the `JAVA_OPTS` environment variable.

  Options are whitespace-separated. Quotes group values containing spaces and
  are removed, like the standalone dumper's launcher scripts do, so the
  documented `set JAVA_OPTS="-Xmx4G"` form works on Windows. Backslashes are
  literal, so Windows paths need no escaping.

  Returns:
    list[str], The JVM options, or an empty list if the variable is unset.

  Raises:
    InvalidJavaOptsError: If the value has unbalanced quotes.
  """
  value = encoding.GetEncodedValue(os.environ, JAVA_OPTS_ENV_VAR, '')
  lexer = shlex.shlex(value, posix=True)
  lexer.whitespace_split = True
  lexer.commenters = ''
  lexer.escape = ''
  try:
    # Drop empty tokens such as the `""` cmd.exe stores for `set JAVA_OPTS=""`.
    return [opt for opt in lexer if opt]
  except ValueError as err:
    # Deliberately omit the value: it may contain a trust-store password.
    raise InvalidJavaOptsError(
        'Unable to parse the {} environment variable: {}.'.format(
            JAVA_OPTS_ENV_VAR, err
        )
    ) from err


def BuildJavaCommand(java_bin, jar_path, main_class, program_args, jvm_opts):
  """Constructs the command line that runs a `bqms` component JAR.

  JVM options come first (the defaults, then the user's, so the user's can
  override them), followed by `-cp <jar> <main class> <program args>`. Keeping
  `-cp` next to the main class means a stray `-cp` in `JAVA_OPTS` cannot
  replace the tool's classpath.

  Args:
    java_bin: str, Path to the Java executable.
    jar_path: str, Path to the JAR file.
    main_class: str, Fully qualified name of the main class to run.
    program_args: list[str], Arguments passed to the main class.
    jvm_opts: list[str], Extra JVM options (see `GetUserJvmOpts`).

  Returns:
    list[str], The command-line arguments list.
  """
  cmd = [java_bin]
  cmd.extend(DEFAULT_JVM_FLAGS)
  cmd.extend(jvm_opts)
  cmd.extend(['-cp', jar_path, main_class])
  cmd.extend(program_args)
  return cmd


def RunJar(
    jar_name,
    main_class,
    for_text,
    program_args,
    env_var=None,
    jvm_opts=None,
    env_overrides=None,
):
  """Runs a `bqms` component JAR on this machine and waits for it to exit.

  Args:
    jar_name: str, Filename of the JAR in the component (e.g. `dumper.jar`).
    main_class: str, Fully qualified name of the main class to run.
    for_text: str, Human-readable name of the tool, used in installation prompts
      and error messages (e.g. 'BigQuery Migration Extractor').
    program_args: list[str], Arguments passed to the main class.
    env_var: str or None, Optional environment variable name that overrides the
      packaged JAR path (see `GetBqmsJarPath`).
    jvm_opts: list[str] or None, Extra JVM options. Read from the `JAVA_OPTS`
      environment variable (see `GetUserJvmOpts`) when None; callers that
      perform RPCs first pass the parsed value so a bad variable fails fast.
    env_overrides: dict[str, str] or None, Environment variables to set for the
      tool process on top of the current environment.

  Raises:
    java.JavaError: If Java `MIN_JAVA_VERSION`+ is not installed.
    local_state.InvalidSDKRootError: If no Cloud SDK root directory is found.
    BqmsJarNotFoundError: If the JAR file cannot be located.
    InvalidJavaOptsError: If the `JAVA_OPTS` environment variable cannot be
      parsed.
    BqmsToolExecutionError: If the tool exits with a non-zero code; the error
      carries that code as the gcloud exit code.
  """
  if jvm_opts is None:
    jvm_opts = GetUserJvmOpts()
  java_bin = java.RequireJavaInstalled(for_text, min_version=MIN_JAVA_VERSION)
  jar_path = GetBqmsJarPath(
      jar_name=jar_name, for_text=for_text, env_var=env_var
  )
  exec_args = BuildJavaCommand(
      java_bin, jar_path, main_class, program_args, jvm_opts
  )

  env = None
  if env_overrides:
    # `execution_utils.Exec` uses the given environment as-is, so extend a
    # copy of the current one rather than passing only the overrides.
    env = dict(os.environ)
    for name, value in env_overrides.items():
      encoding.SetEncodedValue(env, name, value)

  return_code = execution_utils.Exec(exec_args, env=env, no_exit=True)
  if return_code != 0:
    raise BqmsToolExecutionError(
        '{} failed with exit code {}.'.format(for_text, return_code),
        exit_code=return_code,
    )
