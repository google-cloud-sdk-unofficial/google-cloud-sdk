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
"""The create command for BigLake Hive tables."""

import textwrap

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import arguments
from googlecloudsdk.command_lib.biglake import flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files


help_text = textwrap.dedent("""\
    To create a table `my_table` in parent catalog `my-catalog` and database `my-database`
    using a creation request from `table_creation.json`, run:

      $ {command} my_table --database=my-database --catalog=my-catalog --file=table_creation.json

    The storageDescriptor field is required and must be specified in the file.

    Example `table_creation.json`:

      {
        "name": "my_table",
        "storageDescriptor": {
          "locationUri": "gs://my-bucket/my-database/my_table",
          "inputFormat": "org.apache.hadoop.mapred.TextInputFormat",
          "outputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
          "serdeInfo": {
            "name": "my_table",
            "serializationLib": "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"
          },
          "columns": [
            {"name": "id", "type": "int"},
            {"name": "name", "type": "string"}
          ]
        },
        "parameters": {
          "EXTERNAL": "TRUE"
        }
      }
    """)


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA
)
@base.DefaultUniverseOnly
class Create(base.CreateCommand):
  """Create a BigLake Hive table."""

  detailed_help = {
      'EXAMPLES': help_text,
  }

  @classmethod
  def Args(cls, parser):
    flags.AddTableResourceArg(
        parser, 'to create', positional=True, table_type='Hive'
    )
    arguments.AddHiveTableCreateArgs(parser)

  def Run(self, args):
    table_ref = args.CONCEPTS.table.Parse()
    table_id = table_ref.tablesId
    parent_ref = table_ref.Parent()
    parent = parent_ref.RelativeName()

    try:
      file_content = files.ReadFileContents(args.file)
      data = yaml.load(file_content)
    except files.Error as e:
      raise exceptions.Error(
          'Failed to read creation file [{}]: {}'.format(args.file, e)
      )
    except yaml.YAMLParseError as e:
      raise exceptions.Error(
          'Failed to parse YAML/JSON from file [{}]: {}'.format(args.file, e)
      )

    # We use v1beta client for Hive metastore operations.
    client = apis.GetClientInstance('biglake', 'v1beta')
    messages = apis.GetMessagesModule('biglake', 'v1beta')

    try:
      hive_table = encoding.PyValueToMessage(messages.HiveTable, data)
    except Exception as e:
      raise exceptions.Error(
          'Failed to parse HiveTable message from file: {}'.format(e)
      )

    # Clear the name field as it should be the full resource name, which is
    # constructed by the server.
    hive_table.name = None

    # Validate that storageDescriptor is in JSON/YAML.
    if not hive_table.storageDescriptor:
      raise exceptions.Error(
          'Table storageDescriptor must be specified in the file [{}] via '
          'the "storageDescriptor" field.'.format(args.file)
      )

    request = (
        messages.BiglakeHiveV1betaProjectsCatalogsDatabasesTablesCreateRequest(
            parent=parent,
            hiveTableId=table_id,
            hiveTable=hive_table,
        )
    )

    response = client.hive_v1beta_projects_catalogs_databases_tables.Create(
        request
    )

    log.CreatedResource(
        '{}/tables/{}'.format(parent, table_id),
        'table',
    )
    return response
