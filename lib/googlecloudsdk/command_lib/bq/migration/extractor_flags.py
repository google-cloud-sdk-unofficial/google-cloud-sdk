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
"""Flags and help text shared by the BigQuery migration extract commands."""

import argparse
import enum

from googlecloudsdk.command_lib.secrets import args as secrets_args


class ExtractType(enum.Enum):
  """Types of extraction commands under `bq migration * extract`."""

  METADATA = 'metadata'
  QUERY_LOGS = 'query-logs'


_CONNECTOR_HELP = {
    ExtractType.METADATA: (
        'Metadata connector to use for extraction (for example, `snowflake`,'
        ' `teradata`, or `redshift`). Must be a metadata connector, not a query'
        ' logs connector (do not use a `-logs` connector).'
    ),
    ExtractType.QUERY_LOGS: (
        'Query logs connector to use for extraction (for example,'
        ' `snowflake-logs`, `teradata-logs`, `redshift-raw-logs`, or'
        ' `redshift-serverless-logs`). Must be the exact query logs connector'
        ' name expected by the backend, not a metadata connector.'
    ),
}

_DESCRIPTION_HELP = """\
    {description}

    By default (`--run-mode=local`), the extractor runs on this machine and
    writes its output archive to `--output`, which can be either a local file
    or directory path or a Cloud Storage URI (`gs://bucket/path`). Writing to
    Cloud Storage in local mode uses Application Default Credentials (for
    example, from `gcloud auth application-default login`). Local mode requires
    Java 11 or later on your `PATH`; the `bqms` component of the gcloud CLI,
    which contains the extractor, is installed on first use if it is missing. To
    pass additional options to the Java virtual machine, set the `JAVA_OPTS`
    environment variable, for example `export JAVA_OPTS=-Xmx8G` (Linux and
    macOS) or `set JAVA_OPTS=-Xmx8G` (Windows Command Prompt) for large
    extractions, or `-Djavax.net.ssl.trustStore=...` for a custom trust store.

    With `--run-mode=cloud`, the extractor runs on a Compute Engine instance in
    your project instead and writes its output archive to the Cloud Storage URI
    given by `--output`. The forwarded arguments are passed to the instance
    through a Secret Manager secret (see `--secret`); because the instance
    cannot prompt for input, include connection credentials such as
    `--password` in them.

    When `--output` is a Cloud Storage URI (`gs://bucket/path`), the command
    verifies before running the extractor that the bucket belongs to
    `--expected-owner` (or the active `core/project` property if
    `--expected-owner` is not specified) and does not allow public access. This
    requires `storage.buckets.list` permission (for example,
    `roles/storage.bucketViewer`) on the owner project, object write
    permissions (`roles/storage.objectUser` or `roles/storage.objectCreator`) on
    the bucket, and `storage.buckets.getIamPolicy` permission
    (`roles/storage.admin`) on the bucket if Public Access Prevention is not
    enforced on the bucket.

    Arguments after `--` are forwarded to the extractor unchanged. For the
    available connectors and their arguments, see
    https://cloud.google.com/bigquery/docs/generate-metadata.
    """

_EXAMPLES_HELP = {
    ExtractType.METADATA: (
        """\
    To extract Snowflake metadata to `gs://my-bucket/snowflake/` using the
    extractor on this machine (which prompts for the password), run:

      $ {command} --connector=snowflake \\
          --output=gs://my-bucket/snowflake/ -- \\
          --host=my-account.snowflakecomputing.com --user=my-user \\
          --database=MY_DB --warehouse=MY_WH

    To run the same extraction on a Compute Engine instance in zone
    `us-central1-a`, run:

      $ {command} --connector=snowflake \\
          --output=gs://my-bucket/snowflake/ --run-mode=cloud \\
          --zone=us-central1-a -- \\
          --host=my-account.snowflakecomputing.com --user=my-user \\
          --password=my-password --database=MY_DB --warehouse=MY_WH
    """
    ),
    ExtractType.QUERY_LOGS: (
        """\
    To extract the last seven days (the default range) of Snowflake query logs
    to `gs://my-bucket/snowflake-logs/` using the extractor on this machine
    (which prompts for the password), run:

      $ {command} --connector=snowflake-logs \\
          --output=gs://my-bucket/snowflake-logs/ -- \\
          --host=my-account.snowflakecomputing.com --user=my-user \\
          --database=MY_DB --warehouse=MY_WH

    To run the same extraction on a Compute Engine instance in zone
    `us-central1-a`, run:

      $ {command} --connector=snowflake-logs \\
          --output=gs://my-bucket/snowflake-logs/ --run-mode=cloud \\
          --zone=us-central1-a -- \\
          --host=my-account.snowflakecomputing.com --user=my-user \\
          --password=my-password --database=MY_DB --warehouse=MY_WH
    """
    ),
}


def GetDetailedHelp(extract_type):
  """Returns the `detailed_help` dict for a `bq migration * extract` command.

  Args:
    extract_type: ExtractType, the extraction subcommand type.

  Returns:
    dict[str, str], Calliope `detailed_help` sections (DESCRIPTION, EXAMPLES).
  """
  return {
      'DESCRIPTION': _DESCRIPTION_HELP,
      'EXAMPLES': _EXAMPLES_HELP[extract_type],
  }


def AddExtractorFlags(parser, extract_type=ExtractType.METADATA):
  """Adds the flags shared by `bq migration * extract` commands.

  Args:
    parser: argparse.ArgumentParser, the parser to add the flags to.
    extract_type: ExtractType, the extraction subcommand type (for example,
      `ExtractType.METADATA` or `ExtractType.QUERY_LOGS`).
  """
  parser.add_argument(
      '--run-mode',
      choices=['local', 'cloud'],
      default='local',
      help='Run mode for the extractor.',
  )
  parser.add_argument(
      '--output',
      required=True,
      help=(
          'Target path for the extracted archive: a Cloud Storage URI'
          ' (`gs://bucket/path`) or, with `--run-mode=local`, a local file or'
          ' directory path.'
      ),
  )
  parser.add_argument(
      '--connector',
      required=True,
      help=_CONNECTOR_HELP[extract_type],
  )
  parser.add_argument(
      '--expected-owner',
      help=(
          'Expected owner project ID of the `--output` Cloud Storage bucket.'
          ' Defaults to the active `core/project` property.'
      ),
  )

  cloud_group = parser.add_group(
      help='Cloud run mode options (--run-mode=cloud).'
  )
  cloud_group.add_argument(
      '--zone',
      help='Zone to launch Compute Engine instance.',
  )
  secrets_args.AddSecret(
      parser,
      purpose=(
          'used to pass the extractor arguments to the Compute Engine instance'
      ),
      positional=False,
      required=False,
      group=cloud_group,
  )
  cloud_group.add_argument(
      '--gce-instance',
      help='Name of the Compute Engine instance.',
  )
  cloud_group.add_argument(
      '--gce-startup-script-url',
      help='URL to startup script.',
  )
  cloud_group.add_argument(
      '--gce-service-account',
      help='Service account for Compute Engine instance.',
  )
  cloud_group.add_argument(
      '--service-account-user',
      help='User to grant serviceAccountUser role.',
  )
  cloud_group.add_argument(
      '--network',
      help='Network for Compute Engine instance.',
  )
  cloud_group.add_argument(
      '--subnet',
      help='Subnet for Compute Engine instance.',
  )
  cloud_group.add_argument(
      '--no-address',
      action='store_true',
      help='Do not assign external IP to Compute Engine instance.',
  )

  parser.add_argument(
      'dumper_args',
      metavar='EXTRACTOR_ARGS',
      nargs=argparse.REMAINDER,
      help='Arguments forwarded to the extractor.',
  )
