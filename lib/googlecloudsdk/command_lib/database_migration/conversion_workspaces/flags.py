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
"""Flags and helpers for the conversion workspace related commands."""

import argparse
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.database_migration.conversion_workspaces import enums


def AddNoAsyncFlag(parser: argparse.ArgumentParser) -> None:
  """Adds a --no-async flag to the given parser."""
  parser.add_argument(
      '--no-async',
      action='store_true',
      help='Waits for the operation in progress to complete before returning.',
  )


def AddDisplayNameFlag(parser: argparse.ArgumentParser) -> None:
  """Adds a --display-name flag to the given parser."""
  parser.add_argument(
      '--display-name',
      help="""\
        A user-friendly name for the conversion workspace. The display name can
        include letters, numbers, spaces, and hyphens, and must start with a letter.
        The maximum length allowed is 60 characters.
      """,
  )


def AddDatabaseEngineFlags(parser: argparse.ArgumentParser) -> None:
  """Adds database engine flags to the given parser.

  Adds the --source-database-engine and --destination-database-engine flags.

  Args:
    parser: The argparse parser.
  """

  parser.add_argument(
      '--source-database-engine',
      help='Source database engine type.',
      type=enums.SourceDatabaseEngine,
      choices=list(enums.SourceDatabaseEngine),
      required=True,
  )

  parser.add_argument(
      '--destination-database-engine',
      help='Destination database engine type.',
      type=enums.DestinationDatabaseEngine,
      choices=list(enums.DestinationDatabaseEngine),
      required=True,
  )


def AddDatabaseProviderFlags(parser: argparse.ArgumentParser) -> None:
  """Adds database provider flags.

  Adds the --source-database-provider and --destination-database-provider flags
  to the given parser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--source-database-provider',
      help='Source database provider.',
      type=enums.SourceDatabaseProvider,
      choices=list(enums.SourceDatabaseProvider),
      default=enums.SourceDatabaseProvider.UNSPECIFIED.value,
  )

  parser.add_argument(
      '--destination-database-provider',
      help='Destination database provider.',
      type=enums.DestinationDatabaseProvider,
      choices=list(enums.DestinationDatabaseProvider),
      default=enums.DestinationDatabaseProvider.CLOUDSQL.value,
  )


def AddDatabaseVersionFlag(parser: argparse.ArgumentParser) -> None:
  """Adds database version flags to the given parser.

  Adds the --source-database-version and --destination-database-version flags.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--source-database-version',
      help="""\
        Version number for the database engine.
        The version number must contain numbers and letters only.
        Example for Oracle 21c, version number will be 21c.
      """,
      default='unspecified',
  )
  parser.add_argument(
      '--destination-database-version',
      help="""\
        Version number for the database engine.
        The version number must contain numbers and letters only.
        Example for PostgreSQL 17.0, version number will be 17.0.
      """,
      default='unspecified',
  )


def AddGlobalSettingsFlag(parser: argparse.ArgumentParser) -> None:
  """Adds a --global-settings flag to the given parser."""
  parser.add_argument(
      '--global-settings',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help="""\
        A generic list of settings for the workspace. The settings are database pair
        dependant and can indicate default behavior for the mapping rules engine or
        turn on or off specific features. An object containing a list of
        "key": "value" pairs.
      """,
  )


def AddGlobalFilterFlag(parser: argparse.ArgumentParser) -> None:
  """Adds a --global-filter flag to the given parser."""
  parser.add_argument(
      '--global-filter',
      help="""\
        Filter the source entities based on [AIP-160](https://google.aip.dev/160) standard.
        This filter will be applied to all subsequent operations on the source entities,
        such as convert and describe-entities.
      """,
  )


def AddFeatureFlags(parser: argparse.ArgumentParser) -> None:
  """Adds feature flags to the given parser."""
  parser.add_argument(
      '--auto-conversion',
      action=arg_parsers.StoreTrueFalseAction,
      help='Whether to enable Gemini auto-conversion.',
  )
  parser.add_argument(
      '--quality-assessment',
      action=arg_parsers.StoreTrueFalseAction,
      help='Whether to enable Gemini quality assessment.',
  )
  parser.add_argument(
      '--conversion-assistance',
      action=arg_parsers.StoreTrueFalseAction,
      help='Whether to enable Gemini conversion assistance.',
  )
  parser.add_argument(
      '--pattern-matching',
      action=arg_parsers.StoreTrueFalseAction,
      help='Whether to enable Gemini pattern matching.',
  )


def AddCommitNameFlag(parser: argparse.ArgumentParser) -> None:
  """Adds a --commit-name flag to the given parser."""
  parser.add_argument(
      '--commit-name',
      help="""\
        A user-friendly name for the conversion workspace commit. The commit name
        can include letters, numbers, spaces, and hyphens, and must start with a
        letter.
        """,
  )


def AddAutoCommitFlag(parser: argparse.ArgumentParser) -> None:
  """Adds a --auto-commit flag to the given parser."""
  parser.add_argument(
      '--auto-commit',
      action='store_true',
      help='Auto commits the conversion workspace.',
  )


def AddImportFileFormatFlag(parser: argparse.ArgumentParser) -> None:
  """Adds the --file-format flag to the given parser."""
  parser.add_argument(
      '--file-format',
      help='File format type to import rules from.',
      choices=['ORA2PG'],
      default='ORA2PG',
  )


def AddConfigFilesFlag(parser: argparse.ArgumentParser) -> None:
  """Adds a --config-files flag to the given parser."""
  parser.add_argument(
      '--config-files',
      metavar='CONFIG_FILE',
      type=arg_parsers.ArgList(min_length=1),
      help="""\
        A list of files to import rules from. Either provide a single file path or if
        multiple files are to be provided, each file should correspond to one schema.
        Provide file paths as a comma separated list.
      """,
      required=True,
  )


def AddFilterFlag(parser: argparse.ArgumentParser) -> None:
  """Adds a --filter flag to the given parser."""
  parser.add_argument(
      '--filter',
      help="""\
        Filter the entities based on [AIP-160](https://google.aip.dev/160) standard.
        Example:
          to filter all tables whose name start with "Employee" and are present
          under schema "Company", use filter as
            "Company.Employee```*``` AND type=TABLE"
       """,
  )


def AddTreeTypeFlag(
    parser: argparse.ArgumentParser,
    required: bool = True,
    default_value: str = 'DRAFT',
) -> None:
  """Adds the --tree-type flag to the given parser."""
  parser.add_argument(
      '--tree-type',
      help='Tree type for database entities.',
      choices=['SOURCE', 'DRAFT'],
      required=required,
      default=default_value,
  )


def AddUncommittedFlag(parser: argparse.ArgumentParser) -> None:
  """Adds a --uncommitted flag to the given parser."""
  parser.add_argument(
      '--uncommitted',
      action='store_true',
      help="""\
        Whether to retrieve the latest committed version of the entities or the
        latest version.
        This field is ignored if a specific commit_id is specified.
      """,
  )


def AddCommitIdFlag(parser: argparse.ArgumentParser) -> None:
  """Adds a --commit-id flag to the given parser."""
  parser.add_argument(
      '--commit-id',
      help="""\
        Request a specific commit id.
        If not specified, the entities from the latest commit are returned.
       """,
  )


def AddSourceDetailsFlag(parser: argparse.ArgumentParser) -> None:
  """Adds source details to the parser for application code conversion."""

  source_details_group = parser.add_group(required=True, mutex=True)
  AddSourceFolderFlag(source_details_group)
  AddSourceFileFlag(source_details_group)


def AddSourceFolderFlag(parser: argparse.ArgumentParser) -> None:
  """Adds a --source-folder flag to the given parser."""
  parser.add_argument(
      '--source-folder',
      help="""\
        A folder path to the source code files which needs to be converted.
        If the target-path is not specified, the source file is backed up and
        the original file is overwritten with the converted code.
      """,
  )


def AddSourceFileFlag(parser: argparse.ArgumentParser) -> None:
  """Adds a --source-file flag to the given parser."""
  parser.add_argument(
      '--source-file',
      help="""\
        A file path to the source code which needs to be converted.
        If the target-path is not specified, the source file is backed up and
        the original file is overwritten with the converted code.
      """,
  )


def AddTargetPathFlag(parser: argparse.ArgumentParser) -> None:
  """Adds a --target-path flag to the given parser."""
  parser.add_argument(
      '--target-path',
      help="""\
        Path where the converted code should be written.
        This can be a directory or a file name.
        In case it is a directory, the file name will be the same as the source file.
        If it is not provied, source file is backed up and the original file
        is overwritten with the converted code.
      """,
  )


def AddSourceDialectFlag(parser: argparse.ArgumentParser) -> None:
  """Adds a --source-dialect flag to the given parser."""
  parser.add_argument(
      '--source-dialect',
      help=(
          'The source dialect of the code to be converted. This can only be'
          ' ORACLE.'
      ),
      required=True,
  )


def AddTargetDialectFlag(parser: argparse.ArgumentParser) -> None:
  """Adds a --target-dialect flag to the given parser."""
  parser.add_argument(
      '--target-dialect',
      help=(
          'The target dialect of the code to be converted. This can only be'
          ' POSTGRESQL.'
      ),
      required=True,
  )
