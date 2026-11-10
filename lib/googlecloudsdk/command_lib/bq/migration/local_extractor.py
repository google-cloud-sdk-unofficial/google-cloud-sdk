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
"""Local execution mode for BigQuery migration extract commands."""

import os

from googlecloudsdk.command_lib.bq.migration import bqms_utils
from googlecloudsdk.command_lib.bq.migration import extractor_flags
from googlecloudsdk.command_lib.bq.migration import extractor_utils
from googlecloudsdk.command_lib.util import java
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import platforms

DUMPER_JAR_NAME = 'dumper.jar'
DUMPER_JAR_ENV_VAR = 'BQMS_DUMPER_JAR_PATH'
DUMPER_MAIN_CLASS = 'com.google.edwmigration.dumper.application.dumper.Main'
DUMPER_SUBCOMMAND = 'extract'
EXTRACTOR_TITLE = 'BigQuery Migration Extractor'


class DumperExecutionError(exceptions.Error):
  """Raised when the local dumper process exits with a non-zero status."""


def _BuildExtractorArgs(connector, output_uri, dumper_args=None):
  """Returns the `--connector`, `--output`, and forwarded dumper arguments."""
  args = ['--connector', connector, '--output', output_uri]
  args.extend(extractor_utils.CleanDumperArgs(dumper_args))
  return args


def BuildLauncherCommand(
    launcher_path, connector, output_uri, dumper_args=None
):
  """Constructs the command line to invoke the `bqms` component launcher.

  Invokes `<launcher> extract --connector <connector> --output <output> ...`,
  which resolves required JDBC drivers via `validation-client.jar` before
  launching `dumper.jar`.

  Args:
    launcher_path: str, Path to the `bqms` (or `bqms.cmd`) launcher script.
    connector: str, Target connector name.
    output_uri: str, Target Cloud Storage URI (`gs://bucket/path`) or local
      file/directory path.
    dumper_args: list[str] or None, Additional forwarded dumper arguments.

  Returns:
    list[str], The command-line arguments list.
  """
  tool_args = [DUMPER_SUBCOMMAND]
  tool_args.extend(_BuildExtractorArgs(connector, output_uri, dumper_args))
  if platforms.OperatingSystem.IsWindows():
    return execution_utils.ArgsForCMDTool(launcher_path, *tool_args)
  return execution_utils.ArgsForExecutableTool(launcher_path, *tool_args)


def BuildDumperCommand(
    java_bin, jar_path, connector, output_uri, dumper_args=None, jvm_opts=None
):
  """Constructs the command line to invoke the Java dumper.

  JVM options come first (the defaults, then the user's, so the user's can
  override them), followed by `-cp <jar> <main class> <args>`. Keeping `-cp`
  next to the main class means a stray `-cp` in `JAVA_OPTS` cannot replace the
  dumper classpath.

  Args:
    java_bin: str, Path to the Java executable.
    jar_path: str, Path to `dumper.jar`.
    connector: str, Target connector name.
    output_uri: str, Target Cloud Storage URI (`gs://bucket/path`) or local
      file/directory path.
    dumper_args: list[str] or None, Additional forwarded dumper arguments.
    jvm_opts: list[str] or None, Extra JVM options (see
      `bqms_utils.GetUserJvmOpts`).

  Returns:
    list[str], The command-line arguments list.
  """
  cmd = [java_bin]
  cmd.extend(bqms_utils.DEFAULT_JVM_FLAGS)
  cmd.extend(jvm_opts or [])
  cmd.extend(['-cp', jar_path, DUMPER_MAIN_CLASS])
  cmd.extend(_BuildExtractorArgs(connector, output_uri, dumper_args))
  return cmd


def Run(args, extract_type=extractor_flags.ExtractType.METADATA):
  """Executes the migration extractor locally.

  Delegates to the `bqms` component launcher
  (`<sdk_root>/platform/bqms/bin/bqms`
  or `bqms.cmd` on Windows) with the `extract` subcommand so required JDBC
  drivers are resolved automatically, unless `BQMS_DUMPER_JAR_PATH` is set to
  override `dumper.jar` directly.

  Args:
    args: argparse.Namespace, Parsed CLI arguments.
    extract_type: extractor_flags.ExtractType, The extraction subcommand type.

  Raises:
    calliope_exceptions.InvalidArgumentException: If flags or connector are
      invalid.
    extractor_utils.BucketVerificationError: If the output GCS bucket fails
      ownership or public-access checks.
    java.JavaError: If Java 11+ is not installed.
    local_state.InvalidSDKRootError: If no Cloud SDK root directory is found.
    bqms_utils.BqmsLauncherNotFoundError: If the `bqms` launcher script cannot
      be located when `BQMS_DUMPER_JAR_PATH` is not set.
    bqms_utils.BqmsJarNotFoundError: If the custom `dumper.jar` specified by
      `BQMS_DUMPER_JAR_PATH` cannot be located.
    bqms_utils.InvalidJavaOptsError: If the `JAVA_OPTS` environment variable
      cannot be parsed.
    DumperExecutionError: If the dumper subprocess exits with a non-zero code.
  """
  extractor_utils.ValidateLocalModeFlags(args)
  extractor_utils.ValidateConnector(args.connector, extract_type=extract_type)
  jvm_opts = bqms_utils.GetUserJvmOpts()  # Cheap check first, before any RPCs.
  if extractor_utils.IsGcsOutputUri(args.output):
    extractor_utils.VerifyOutputBucket(
        args.output, expected_owner=args.expected_owner
    )
  else:
    extractor_utils.ValidateLocalOutputPath(
        args.output, expected_owner=args.expected_owner
    )

  java_bin = java.RequireJavaInstalled(
      EXTRACTOR_TITLE, min_version=bqms_utils.MIN_JAVA_VERSION
  )
  if encoding.GetEncodedValue(os.environ, DUMPER_JAR_ENV_VAR):
    jar_path = bqms_utils.GetBqmsJarPath(
        jar_name=DUMPER_JAR_NAME,
        for_text=EXTRACTOR_TITLE,
        env_var=DUMPER_JAR_ENV_VAR,
    )
    exec_args = BuildDumperCommand(
        java_bin=java_bin,
        jar_path=jar_path,
        connector=args.connector,
        output_uri=args.output,
        dumper_args=args.dumper_args,
        jvm_opts=jvm_opts,
    )
  else:
    launcher_path = bqms_utils.GetBqmsLauncherPath(for_text=EXTRACTOR_TITLE)
    exec_args = BuildLauncherCommand(
        launcher_path=launcher_path,
        connector=args.connector,
        output_uri=args.output,
        dumper_args=args.dumper_args,
    )

  log.status.Print(
      'Running {} locally with connector [{}]...'.format(
          EXTRACTOR_TITLE, args.connector
      )
  )
  return_code = execution_utils.Exec(exec_args, no_exit=True)
  if return_code != 0:
    raise DumperExecutionError(
        '{} failed with exit code {}.'.format(EXTRACTOR_TITLE, return_code)
    )
