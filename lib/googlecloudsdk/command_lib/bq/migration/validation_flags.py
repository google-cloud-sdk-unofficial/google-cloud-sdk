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
"""Flags of the `bq migration validation` commands and their client mapping.

Each `Add*Flags` function registers the flags of one command, and the matching
`Get*ClientArgs` function translates the parsed arguments into the arguments
of the corresponding validation client subcommand (see `validation_client`).
"""

import argparse
import os

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.bq.migration import validation_client
from googlecloudsdk.core.console import console_io


def AddClientArgsFlag(parser):
  """Adds the `-- CLIENT_ARGS` pass-through positional."""
  parser.add_argument(
      'client_args',
      metavar='CLIENT_ARGS',
      nargs=argparse.REMAINDER,
      help='Arguments forwarded to the validation client.',
  )


def AddConfigureFlags(parser):
  """Adds the flags of `bq migration validation configure`.

  Args:
    parser: argparse.ArgumentParser, the parser to add the flags to.
  """
  parser.add_argument(
      '--output',
      required=True,
      metavar='DIRECTORY',
      help=(
          'Directory to write the configuration files to. Fails if the'
          ' directory already contains files, unless `--force` is specified.'
      ),
  )
  inputs = parser.add_group(
      required=True,
      help=(
          'Source table definitions to generate the configuration from. Both'
          ' can be combined.'
      ),
  )
  inputs.add_argument(
      '--metadata',
      metavar='PATH',
      help=(
          'Path to a source metadata archive (a `.zip` file produced by'
          ' `gcloud alpha bq migration metadata extract`), or to a directory'
          ' containing such archives and `tables.yaml` translation mapping'
          ' files.'
      ),
  )
  inputs.add_argument(
      '--tables-yaml',
      type=arg_parsers.ArgList(),
      metavar='PATH',
      help=(
          'Paths to `tables.yaml` mapping files produced by BigQuery'
          ' Migration Service SQL translation, or to directories containing'
          ' them.'
      ),
  )
  parser.add_argument(
      '--target-dataset',
      help=(
          'BigQuery dataset that contains the migrated tables. Defaults to a'
          ' dataset named like the schema of each source table.'
      ),
  )
  parser.add_argument(
      '--schemas',
      type=arg_parsers.ArgList(),
      metavar='SCHEMA',
      help='Only generate configuration for tables in these source schemas.',
  )
  parser.add_argument(
      '--tables',
      type=arg_parsers.ArgList(),
      metavar='TABLE',
      help='Only generate configuration for these source tables.',
  )
  parser.add_argument(
      '--force',
      action='store_true',
      help='Overwrite existing configuration files in `--output`.',
  )
  AddClientArgsFlag(parser)


def _RequireNonEmpty(value, flag_name, description):
  """Raises InvalidArgumentException if `value` is empty or whitespace-only."""
  if not value or not value.strip():
    raise calliope_exceptions.InvalidArgumentException(
        flag_name, '{} cannot be empty.'.format(description)
    )


def _RequireNonEmptyList(values, flag_name, item_description):
  """Raises InvalidArgumentException if `values` is empty or has blank items."""
  if not values:
    raise calliope_exceptions.InvalidArgumentException(
        flag_name, 'At least one {} must be specified.'.format(item_description)
    )
  for item in values:
    _RequireNonEmpty(item, flag_name, item_description.capitalize())


def _GetMetadataClientArgs(path):
  """Returns the `generate-config` arguments for the `--metadata` path."""
  _RequireNonEmpty(path, '--metadata', 'Metadata path')
  if not os.path.exists(path):
    raise calliope_exceptions.InvalidArgumentException(
        '--metadata', 'Path [{}] does not exist.'.format(path)
    )
  if os.path.isdir(path):
    return ['--metadata-dir', path]
  if not os.path.isfile(path) or not path.lower().endswith('.zip'):
    raise calliope_exceptions.InvalidArgumentException(
        '--metadata',
        'Path [{}] must be a .zip archive or a directory.'.format(path),
    )
  return ['--zip', path]


def GetConfigureClientArgs(args):
  """Maps the `configure` arguments to `generate-config` client arguments.

  Args:
    args: argparse.Namespace, Parsed `configure` arguments.

  Returns:
    list[str], The `generate-config` subcommand arguments.

  Raises:
    calliope_exceptions.InvalidArgumentException: If `--output`, `--metadata`,
      `--tables-yaml`, `--target-dataset`, `--schemas`, or `--tables` is
      invalid.
  """
  _RequireNonEmpty(args.output, '--output', 'Output directory')
  client_args = ['--output-dir', args.output]
  if args.metadata is not None:
    client_args.extend(_GetMetadataClientArgs(args.metadata))
  if args.tables_yaml is not None:
    _RequireNonEmptyList(args.tables_yaml, '--tables-yaml', 'tables.yaml path')
    for path in args.tables_yaml:
      client_args.extend(['--tables-yaml', path])
  if args.target_dataset is not None:
    _RequireNonEmpty(args.target_dataset, '--target-dataset', 'Target dataset')
    client_args.extend(['--target-dataset', args.target_dataset])
  if args.schemas is not None:
    _RequireNonEmptyList(args.schemas, '--schemas', 'schema name')
    for schema in args.schemas:
      client_args.extend(['--schemas', schema])
  if args.tables is not None:
    _RequireNonEmptyList(args.tables, '--tables', 'table name')
    for table in args.tables:
      client_args.extend(['--tables', table])
  if args.force:
    client_args.append('--force')
  forwarded_args = args.client_args or []
  if not console_io.CanPrompt() and not validation_client.HasForwardedOption(
      forwarded_args, '--non-interactive'
  ):
    # Mirrors gcloud's own prompting rules (`--quiet`, non-interactive
    # terminals) so the client falls back to defaults instead of hanging. A
    # forwarded `--non-interactive` takes precedence, as the client rejects an
    # option that is specified more than once.
    client_args.append('--non-interactive')
  client_args.extend(validation_client.GetLoggingArgs(forwarded_args))
  client_args.extend(forwarded_args)
  return client_args


# Validation types accepted by `--validation-types`, in the order the client
# documents them, and the client flag each one maps to.
VALIDATION_TYPE_FLAGS = {
    'schema': '--schema',
    'aggregate': '--aggregate',
    'data': '--data',
}


def AddRunFlags(parser):
  """Adds the flags of `bq migration validation run`.

  Args:
    parser: argparse.ArgumentParser, the parser to add the flags to.
  """
  parser.add_argument(
      'config_paths',
      metavar='CONFIG_PATH',
      nargs='+',
      help=(
          'Paths or glob patterns of the configuration files or directories'
          ' generated by `gcloud alpha bq migration validation configure`.'
      ),
  )
  parser.add_argument(
      '--location',
      required=True,
      help=(
          'Location of the BigQuery Migration Service validation workflows'
          ' (for example, `us` or `europe-west1`).'
      ),
  )
  parser.add_argument(
      '--gcs-path',
      help=(
          'Cloud Storage path (`gs://bucket/path`) where the source samples'
          ' are staged. Overrides the path in the configuration.'
      ),
  )
  parser.add_argument(
      '--tables',
      type=arg_parsers.ArgList(),
      metavar='TABLE',
      help=(
          'Only validate these tables. A table matches by its full source or'
          ' target name or by a dot-separated suffix of either (for example,'
          ' `orders` or `sales.orders`).'
      ),
  )
  parser.add_argument(
      '--labels',
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE',
      help='Labels to attach to the validation run.',
  )
  parser.add_argument(
      '--validation-types',
      type=arg_parsers.ArgList(choices=list(VALIDATION_TYPE_FLAGS)),
      metavar='TYPE',
      help=(
          'Validations to run: `schema` compares the table schemas,'
          ' `aggregate` compares column aggregates, and `data` compares'
          ' sampled rows. Defaults to all of them.'
      ),
  )
  AddClientArgsFlag(parser)


def GetRunClientArgs(args):
  """Maps the `run` arguments to `validate` client arguments.

  Args:
    args: argparse.Namespace, Parsed `run` arguments.

  Returns:
    list[str], The `validate` subcommand arguments.

  Raises:
    calliope_exceptions.InvalidArgumentException: If `CONFIG_PATH`,
      `--gcs-path`, `--tables`, `--labels`, or `--validation-types` is invalid.
  """
  _RequireNonEmptyList(args.config_paths, 'CONFIG_PATH', 'configuration path')
  # The configuration paths come first: the client's list flags (`--tables`)
  # would otherwise swallow them as values.
  client_args = list(args.config_paths)
  if args.gcs_path is not None:
    _RequireNonEmpty(args.gcs_path, '--gcs-path', 'Cloud Storage path')
    client_args.extend(['--gcs-path', args.gcs_path])
  if args.tables is not None:
    _RequireNonEmptyList(args.tables, '--tables', 'table name')
    for table in args.tables:
      client_args.extend(['--tables', table])
  if args.labels is not None:
    if not args.labels:
      raise calliope_exceptions.InvalidArgumentException(
          '--labels', 'At least one label must be specified.'
      )
    for key, value in sorted(args.labels.items()):
      _RequireNonEmpty(key, '--labels', 'Label key')
      client_args.extend(['--labels', '{}={}'.format(key, value)])
  if args.validation_types is not None:
    _RequireNonEmptyList(
        args.validation_types, '--validation-types', 'validation type'
    )
    for validation_type in args.validation_types:
      client_args.append(VALIDATION_TYPE_FLAGS[validation_type])
  forwarded_args = args.client_args or []
  client_args.extend(validation_client.GetLoggingArgs(forwarded_args))
  client_args.extend(forwarded_args)
  return client_args


def GetRunClientEnv(args):
  """Returns the environment variables passing gcloud settings to the client.

  Args:
    args: argparse.Namespace, Parsed `run` arguments.

  Returns:
    dict[str, str], Environment variables for the client process: the
    workflow location and, when a regional endpoint (`--endpoint-mode`) or
    `api_endpoint_overrides/bigquerymigration` is active, the resolved
    BigQuery Migration Service endpoint.

  Raises:
    calliope_exceptions.InvalidArgumentException: If `--location` is empty.
  """
  _RequireNonEmpty(args.location, '--location', 'Location')
  location = args.location.strip().lower()
  env = {validation_client.LOCATION_ENV_VAR: location}
  endpoint = apis.GetEffectiveApiEndpoint(
      'bigquerymigration', 'v2', location=location
  )
  default_endpoint = apis.UniversifyAddress(
      apis.GetClientClass('bigquerymigration', 'v2').BASE_URL
  )
  if endpoint != default_endpoint:
    env[validation_client.API_ENDPOINT_ENV_VAR] = endpoint
  return env
