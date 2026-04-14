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
"""The create command for BigLake Iceberg REST catalogs tables."""

import json
import textwrap

from googlecloudsdk.api_lib.biglake import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.biglake import arguments
from googlecloudsdk.command_lib.biglake import flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


help_text = textwrap.dedent("""\
    To create a table `my_table` in parent catalog `my-catalog` and namespace `my-namespace`
    using a creation request from `table_creation.json`, run:

      $ {command} --namespace=my-namespace --catalog=my-catalog --create-from-file=table_creation.json

    The table name and schema fields are required and must be specified in `table_creation.json`.

    Example `table_creation.json`:

      {
        "name": "my_table",
        "location": "gs://my-catalog/my-namespace/my_table",
        "schema": {
          "type": "struct",
          "schema-id": 0,
          "fields": [
            {
              "id": 1,
              "name": "user_id",
              "required": true,
              "type": "long",
              "doc": "Unique identifier for the user"
            },
            {
              "id": 2,
              "name": "username",
              "required": false,
              "type": "string"
            }
          ]
        },
        "partition-spec": {
          "spec-id": 0,
          "fields": [
            {
              "name": "user_id_bucket",
              "transform": "bucket[5]",
              "source-id": 1,
              "partition-id": 1001
            }
          ]
        },
        "write-order": {
          "order-id": 0,
          "fields": [
            {
              "transform": "identity",
              "source-id": 1,
              "direction": "asc",
              "null-order": "nulls-last"
            }
          ]
        },
        "stage-create": false,
        "properties": {
          "owner": "owner",
          "environment": "test",
          "write.format.default": "parquet",
          "comment": "Creating a new table"
        }
      }


    """)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.DefaultUniverseOnly
class Create(base.CreateCommand):
  """Create a BigLake Iceberg table."""

  detailed_help = {
      'EXAMPLES': help_text,
  }

  @classmethod
  def Args(cls, parser):
    flags.AddNamespaceResourceArg(parser, 'to create', positional=False)
    arguments.AddTableCreateArgs(parser)

  def Run(self, args):
    namespace_ref = args.CONCEPTS.namespace.Parse()

    try:
      json_content = files.ReadFileContents(args.create_from_file)
      data = json.loads(json_content)
    except files.Error as e:
      raise exceptions.Error(
          'Failed to read creation file [{}]: {}'.format(
              args.create_from_file, e
          )
      )
    except ValueError as e:
      raise exceptions.Error(
          'Failed to parse JSON from file [{}]: {}'.format(
              args.create_from_file, e
          )
      )

    # Validate that the name is in JSON.
    if 'name' not in data:
      raise exceptions.Error(
          'Table name must be specified in the JSON file [{}] via the "name" '
          'field.'.format(args.create_from_file)
      )
    table_id = data['name']

    # Validate that the schema is in JSON.
    if 'schema' not in data:
      raise exceptions.Error(
          'Table schema must be specified in the JSON file [{}] via the '
          '"schema" field.'.format(args.create_from_file)
      )

    # Iceberg REST API is OSS compliant, so it actually sends and/or receives a
    # raw HTTP body not protos. There is trouble setting and accessing those
    # HTTP body fields without manual creation.
    response_json = util.CreateTable(
        namespace_ref.catalogsId, namespace_ref.namespacesId, data
    )
    response = json.loads(response_json)

    log.CreatedResource(
        util.GetTableName(
            namespace_ref.catalogsId, namespace_ref.namespacesId, table_id
        ),
        'table',
    )
    return response
