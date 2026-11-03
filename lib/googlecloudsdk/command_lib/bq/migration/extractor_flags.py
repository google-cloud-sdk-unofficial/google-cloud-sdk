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
"""Flags shared by the BigQuery migration extract commands."""

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
      help='Cloud Storage target (gs://bucket/path).',
  )
  parser.add_argument(
      '--connector',
      required=True,
      help=_CONNECTOR_HELP[extract_type],
  )
  parser.add_argument(
      '--expected-owner',
      help='Expected owner project of Cloud Storage bucket.',
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
          'used to pass the dumper arguments to the Compute Engine instance'
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
      nargs=argparse.REMAINDER,
      help='Arguments forwarded to the dumper.',
  )
