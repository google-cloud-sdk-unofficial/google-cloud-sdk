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
"""Runs the BigQuery Migration Validation Client packaged in `bqms`."""

import logging

from googlecloudsdk.command_lib.bq.migration import bqms_utils
from googlecloudsdk.core import log

VALIDATION_CLIENT_JAR_NAME = 'validation-client.jar'
VALIDATION_CLIENT_JAR_ENV_VAR = 'BQMS_VALIDATION_CLIENT_JAR_PATH'
VALIDATION_CLIENT_MAIN_CLASS = (
    'com.google.cloud.veritas.validation.apps.client.ClientMain'
)
VALIDATION_CLIENT_TITLE = 'BigQuery Migration Validation Client'

# Subcommands of the validation client.
GENERATE_CONFIG_SUBCOMMAND = 'generate-config'
VALIDATE_SUBCOMMAND = 'validate'

# Environment variables read by the `validate` subcommand: the location of the
# BigQuery Migration Service workflows it creates and the API endpoint.
LOCATION_ENV_VAR = 'BQMS_VALIDATION_LOCATION'
API_ENDPOINT_ENV_VAR = 'BQMS_MIGRATION_API_ENDPOINT'


def HasForwardedOption(forwarded_args, *option_names):
  """Returns True if any of `option_names` is present in `forwarded_args`."""
  for arg in forwarded_args:
    for name in option_names:
      if arg == name or arg.startswith(name + '='):
        return True
  return False


def GetLoggingArgs(forwarded_args=()):
  """Returns the client logging flags matching the gcloud `--verbosity`.

  Args:
    forwarded_args: Sequence[str], Arguments the user forwards to the client.
      Any logging flag among them (or its short alias) takes precedence and
      suppresses the gcloud-derived logging flag.

  Returns:
    list[str], `['--debug']` for debug verbosity, `['--verbose']` for info
    verbosity, and `[]` otherwise (the client then shows its status console).
  """
  if HasForwardedOption(forwarded_args, '--debug', '-d', '--verbose', '-v'):
    return []

  verbosity = log.GetVerbosity()
  if verbosity <= logging.DEBUG:
    return ['--debug']
  elif verbosity <= logging.INFO:
    return ['--verbose']
  return []


def Run(subcommand, client_args, env_overrides=None):
  """Runs a validation client subcommand on this machine.

  Args:
    subcommand: str, The client subcommand (`generate-config` or `validate`).
    client_args: list[str], Arguments for the subcommand.
    env_overrides: dict[str, str] or None, Environment variables to set for the
      client process on top of the current environment.

  Raises:
    java.JavaError: If Java 11+ is not installed.
    local_state.InvalidSDKRootError: If no Cloud SDK root directory is found.
    bqms_utils.BqmsJarNotFoundError: If `validation-client.jar` cannot be
      located.
    bqms_utils.InvalidJavaOptsError: If the `JAVA_OPTS` environment variable
      cannot be parsed.
    bqms_utils.BqmsToolExecutionError: If the client exits with a non-zero
      code.
  """
  log.status.Print('Running {}...'.format(VALIDATION_CLIENT_TITLE))
  bqms_utils.RunJar(
      jar_name=VALIDATION_CLIENT_JAR_NAME,
      main_class=VALIDATION_CLIENT_MAIN_CLASS,
      for_text=VALIDATION_CLIENT_TITLE,
      program_args=[subcommand] + list(client_args),
      env_var=VALIDATION_CLIENT_JAR_ENV_VAR,
      env_overrides=env_overrides,
  )
