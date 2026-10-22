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
"""Spanner cli library functions and utilities for the spanner binary."""

import copy
import os

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.util.anthos import binary_operations
from googlecloudsdk.core import exceptions as c_except
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log

# default base command is sql
_BASE_COMMAND = "sql"
_SPANNER_CLI_BINARY = "spanner-cli"
_NON_COMPONENT_BINARY_WARNING = (
    "`gcloud spanner cli` ran [%s] from your PATH because the `spanner-cli`"
    " component is not installed. This binary may be incompatible with gcloud"
    " (for example, the open-source spanner-cli). To use the supported Spanner"
    " CLI, install the component (it takes precedence over your PATH):\n"
    "  $ gcloud components install spanner-cli"
)


def GetEnvArgsForCommand(extra_vars=None, exclude_vars=None):
  """Return an env dict to be passed on command invocation."""
  env = copy.deepcopy(os.environ)
  if extra_vars:
    env.update(extra_vars)
  if exclude_vars:
    for key in exclude_vars:
      env.pop(key)
  return env


class SpannerCliException(c_except.Error):
  """Base Exception for any errors raised by gcloud spanner cli surface."""


class SpannerCliWrapper(binary_operations.BinaryBackedOperation):
  """Wrapper for spanner cli commands which calls the spanner binary."""

  def __init__(self, **kwargs):
    super(SpannerCliWrapper, self).__init__(
        binary=_SPANNER_CLI_BINARY,
        install_if_missing=True,
        **kwargs,
    )

  def _ParseArgsForCommand(
      self,
      project=None,
      database=None,
      instance=None,
      database_role=None,
      host=None,
      port=None,
      api_endpoint=None,
      idle_transaction_timeout=None,
      skip_column_names=False,
      skip_system_command=False,
      system_command="OFF",
      prompt=None,
      delimiter=None,
      table=False,
      html=False,
      xml=False,
      execute=None,
      source=None,
      tee=None,
      init_command=None,
      init_command_add=None,
      verbose=False,
      directed_read=None,
      proto_descriptor_file=None,
      **kwargs,
  ):
    del kwargs

    formatted_arguments = (_BASE_COMMAND,)

    if project:
      formatted_arguments += (f"--project={project}",)
    if database:
      formatted_arguments += (f"--database={database}",)
    if instance:
      formatted_arguments += (f"--instance={instance}",)
    if database_role:
      formatted_arguments += (f"--role={database_role}",)
    if port and host:
      formatted_arguments += (f"--deployment-endpoint={host}:{port}",)
    elif api_endpoint:
      formatted_arguments += (f"--deployment-endpoint={api_endpoint}",)
    if idle_transaction_timeout:
      formatted_arguments += (
          f"--idle-transaction-timeout={idle_transaction_timeout}",
      )
    if skip_column_names:
      formatted_arguments += ("--skip-column-names",)
    if skip_system_command or system_command == "OFF":
      formatted_arguments += ("--skip-system-command",)
    if prompt:
      formatted_arguments += (f"--prompt={prompt}",)
    if delimiter:
      formatted_arguments += (f"--delimiter={delimiter}",)
    if table:
      formatted_arguments += ("--table",)
    if html:
      formatted_arguments += ("--html",)
    if xml:
      formatted_arguments += ("--xml",)
    if execute:
      formatted_arguments += (f"--execute={execute}",)
    if source:
      formatted_arguments += (f"--source={source}",)
    if tee:
      formatted_arguments += (f"--tee={tee}",)
    if init_command:
      formatted_arguments += (f"--init-command={init_command}",)
    if init_command_add:
      formatted_arguments += (f"--init-command-add={init_command_add}",)
    if verbose:
      formatted_arguments += ("--verbose",)
    if directed_read:
      formatted_arguments += (f"--directed-read={directed_read}",)
    if proto_descriptor_file:
      formatted_arguments += (
          f"--proto-descriptor-file={proto_descriptor_file}",
      )

    return formatted_arguments

  def _Execute(self, cmd, stdin=None, env=None, **kwargs):
    """Executes the spanner-cli binary; exits with child status on failure."""
    exit_code = execution_utils.Exec(cmd, no_exit=True)
    if exit_code != 0:
      is_component = binary_operations.CheckBinaryComponentInstalled(
          _SPANNER_CLI_BINARY
      )
      if is_component is not None and not is_component:
        log.warning(_NON_COMPONENT_BINARY_WARNING, cmd[0])
      raise calliope_exceptions.ExitCodeNoError(exit_code=exit_code)
